from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Material, MaterialPrice, MixRatio, Project, ProjectBlock
from .services import estimate_block


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('adel', 'adel@example.com', 'S0me-strong-pass', full_name='Adel')
        self.client.force_login(self.user)

    def approve_price(self, material_name, price, unit=None):
        material = Material.objects.get(name=material_name)
        return MaterialPrice.objects.create(
            material=material, price=Decimal(price), unit=unit or material.base_unit,
            status=MaterialPrice.Status.APPROVED, created_by=self.user,
            reviewed_by=self.user, reviewed_at=timezone.now(),
        )

    def load_cape_town_prices(self):
        self.approve_price('Sand', '16.43')
        self.approve_price('Stone 13mm', '21.75')
        self.approve_price('Cement 50kg', '85.00')


class EstimateTests(BaseTestCase):
    def options_for(self, quantity, block_type='F'):
        project = Project.objects.create(name='Test', created_by=self.user)
        block = ProjectBlock.objects.create(project=project, block_type=block_type, quantity=quantity)
        return {o['mix'].name: o for o in estimate_block(block)}

    def test_cost_per_block_for_seeded_batches(self):
        self.load_cape_town_prices()
        options = self.options_for(70)
        # Batch 1: (3 x 16.43 + 85) / 22
        self.assertEqual(options['Batch 1']['cost_per_block'], Decimal('6.10'))
        # Batch 2: (3 x 16.43 + 2 x 21.75 + 85) / 35
        self.assertEqual(options['Batch 2']['cost_per_block'], Decimal('5.08'))
        self.assertEqual(options['Batch 3']['cost_per_block'], Decimal('5.16'))
        self.assertEqual(options['Batch 4 (optimum)']['cost_per_block'], Decimal('5.76'))

    def test_batches_round_up(self):
        self.load_cape_town_prices()
        option = self.options_for(70)['Batch 4 (optimum)']
        self.assertEqual(option['batches'], 3)  # 70 / 28 -> 3 batches
        self.assertEqual(option['blocks_produced'], 84)
        self.assertEqual(option['total'], Decimal('484.08'))  # 3 x 161.36

    def test_cheapest_is_flagged(self):
        self.load_cape_town_prices()
        options = self.options_for(35)
        self.assertTrue(options['Batch 2'].get('cheapest'))

    def test_pending_price_is_not_used(self):
        self.approve_price('Sand', '16.43')
        self.approve_price('Stone 13mm', '21.75')
        MaterialPrice.objects.create(
            material=Material.objects.get(name='Cement 50kg'), price=Decimal('85'), unit='bag',
            created_by=self.user,
        )
        option = self.options_for(22)['Batch 1']
        self.assertIsNone(option['total'])
        self.assertEqual(option['missing_prices'], ['Cement 50kg'])

    def test_cubic_metre_price_is_divided_by_16(self):
        self.approve_price('Sand', '262.88', unit='m3')  # 262.88 / 16 = 16.43
        self.approve_price('Cement 50kg', '85.00')
        option = self.options_for(22)['Batch 1']
        self.assertEqual(option['total'], Decimal('134.29'))

    def test_no_mixes_for_half_blocks_yet(self):
        self.assertEqual(self.options_for(10, block_type='H'), {})


class ViewTests(BaseTestCase):
    def test_create_project_redirects_to_results(self):
        response = self.client.post(reverse('home'), {
            'name': 'House', 'description': '', 'half_quantity': '0', 'full_quantity': '500',
        })
        project = Project.objects.get(name='House')
        self.assertRedirects(response, reverse('project_detail', args=[project.pk]))
        self.assertEqual(list(project.blocks.values_list('block_type', 'quantity')), [('F', 500)])

    def test_create_project_requires_blocks(self):
        response = self.client.post(reverse('home'), {'name': 'House', 'half_quantity': '0', 'full_quantity': '0'})
        self.assertContains(response, 'Enter the number of half or full blocks.')
        self.assertFalse(Project.objects.exists())

    def test_results_page_shows_prices(self):
        self.load_cape_town_prices()
        project = Project.objects.create(name='House', created_by=self.user)
        ProjectBlock.objects.create(project=project, block_type='F', quantity=70)
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(response, 'Batch 4 (optimum)')
        self.assertContains(response, '484.08')

    def test_create_mix_with_ingredients(self):
        sand = Material.objects.get(name='Sand')
        response = self.client.post(reverse('mix_new'), {
            'name': 'Half mix', 'block_type': 'H', 'strength_mpa': '5', 'blocks_per_batch': '40', 'is_active': 'on',
            'ingredients-TOTAL_FORMS': '1', 'ingredients-INITIAL_FORMS': '0',
            'ingredients-0-material': sand.pk, 'ingredients-0-quantity': '3',
        })
        self.assertRedirects(response, reverse('config'))
        mix = MixRatio.objects.get(name='Half mix')
        self.assertEqual(mix.ingredients.get().unit, 'wheelbarrow')

    def test_creator_cannot_approve_price(self):
        price = MaterialPrice.objects.create(
            material=Material.objects.get(name='Sand'), price=Decimal('16'), unit='wheelbarrow', created_by=self.user,
        )
        response = self.client.post(reverse('price_review', args=[price.pk]), {'decision': 'approved'})
        self.assertEqual(response.status_code, 403)

    def test_accountant_can_approve_price(self):
        self.user.role = User.Role.ACCOUNTANT
        self.user.save()
        price = MaterialPrice.objects.create(
            material=Material.objects.get(name='Sand'), price=Decimal('16'), unit='wheelbarrow', created_by=self.user,
        )
        self.client.post(reverse('price_review', args=[price.pk]), {'decision': 'approved'})
        price.refresh_from_db()
        self.assertEqual(price.status, MaterialPrice.Status.APPROVED)
        self.assertEqual(price.reviewed_by, self.user)
