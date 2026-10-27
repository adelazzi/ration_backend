from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Material, MaterialPrice, MixRatio, Project, ProjectBlock
from .services import estimate_block, estimate_project, latest_approved_prices


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'adel', 'adel@example.com', 'S0me-strong-pass', full_name='Adel', role=User.Role.MANAGER,
        )
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

    def test_seeded_mixes_apply_to_half_and_full_blocks(self):
        self.assertEqual(len(self.options_for(10, block_type='H')), 4)
        self.assertEqual(len(self.options_for(10, block_type='F')), 4)

    def test_half_only_mix_is_not_offered_for_full_blocks(self):
        MixRatio.objects.create(name='Half only', block_type='H', blocks_per_batch=40)
        self.assertIn('Half only', self.options_for(10, block_type='H'))
        self.assertNotIn('Half only', self.options_for(10, block_type='F'))


class ViewTests(BaseTestCase):
    def test_create_project_redirects_to_results(self):
        response = self.client.post(reverse('project_new'), {
            'name': 'House', 'description': '', 'half_quantity': '0', 'full_quantity': '500',
        })
        project = Project.objects.get(name='House')
        self.assertRedirects(response, reverse('project_detail', args=[project.pk]))
        self.assertEqual(list(project.blocks.values_list('block_type', 'quantity')), [('F', 500)])

    def test_create_project_requires_blocks(self):
        response = self.client.post(reverse('project_new'), {'name': 'House', 'half_quantity': '0', 'full_quantity': '0'})
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

    def test_add_price_then_config_page_lists_it(self):
        sand = Material.objects.get(name='Sand')
        response = self.client.post(reverse('price_add'), {
            'price-material': sand.pk, 'price-price': '150', 'price-price_unit': 'base', 'price-currency': 'ZAR',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'sent for approval')
        self.assertContains(response, 'R 150.00 <span class="muted small">per wheelbarrow</span>', html=False)

    def test_manager_cannot_approve_price(self):
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


class RoleTests(BaseTestCase):
    def as_role(self, role):
        user = User.objects.create_user(f'{role}1', f'{role}@example.com', 'S0me-strong-pass', role=role)
        self.client.force_login(user)
        return user

    def make_project(self, status=Project.Status.DRAFT):
        project = Project.objects.create(name=f'{status} job', created_by=self.user, status=status)
        ProjectBlock.objects.create(project=project, block_type='F', quantity=100)
        return project

    def pending_price(self):
        return MaterialPrice.objects.create(
            material=Material.objects.get(name='Sand'), price=Decimal('20'), unit='wheelbarrow', created_by=self.user,
        )

    def test_home_redirects_to_project_list(self):
        self.assertRedirects(self.client.get(reverse('home')), reverse('project_list'))

    def test_project_list_shows_all_projects_to_manager(self):
        self.make_project()
        self.make_project(Project.Status.APPROVED)
        response = self.client.get(reverse('project_list'))
        self.assertContains(response, 'draft job')
        self.assertContains(response, 'approved job')

    def test_project_list_filters_by_status_and_search(self):
        self.make_project()
        self.make_project(Project.Status.APPROVED)
        response = self.client.get(reverse('project_list'), {'status': 'approved'})
        self.assertNotContains(response, 'draft job')
        response = self.client.get(reverse('project_list'), {'q': 'draft'})
        self.assertNotContains(response, 'approved job')

    def test_creator_sees_only_approved_projects(self):
        draft = self.make_project()
        approved = self.make_project(Project.Status.APPROVED)
        self.as_role(User.Role.CREATOR)
        response = self.client.get(reverse('project_list'))
        self.assertContains(response, 'approved job')
        self.assertNotContains(response, 'draft job')
        self.assertEqual(self.client.get(reverse('project_detail', args=[draft.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('project_detail', args=[approved.pk])).status_code, 200)

    def test_only_manager_can_create_edit_and_delete(self):
        project = self.make_project()
        mix = MixRatio.objects.first()
        for role in (User.Role.ACCOUNTANT, User.Role.CREATOR):
            self.as_role(role)
            self.assertEqual(self.client.get(reverse('project_new')).status_code, 403)
            self.assertEqual(self.client.get(reverse('project_edit', args=[project.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse('project_delete', args=[project.pk])).status_code, 403)
            self.assertEqual(self.client.get(reverse('mix_edit', args=[mix.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse('mix_delete', args=[mix.pk])).status_code, 403)
            self.assertEqual(self.client.post(reverse('price_add'), {}).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.assertTrue(MixRatio.objects.filter(pk=mix.pk).exists())

    def test_accountant_can_view_config_but_creator_cannot(self):
        self.as_role(User.Role.ACCOUNTANT)
        self.assertEqual(self.client.get(reverse('config')).status_code, 200)
        self.as_role(User.Role.CREATOR)
        self.assertEqual(self.client.get(reverse('config')).status_code, 403)

    def test_manager_edits_project_status_and_blocks(self):
        project = self.make_project()
        response = self.client.post(reverse('project_edit', args=[project.pk]), {
            'name': 'Renamed', 'description': '', 'status': 'approved',
            'full_quantity': '0', 'half_quantity': '40',
        })
        self.assertRedirects(response, reverse('project_detail', args=[project.pk]))
        project.refresh_from_db()
        self.assertEqual((project.name, project.status), ('Renamed', 'approved'))
        self.assertEqual(list(project.blocks.values_list('block_type', 'quantity')), [('H', 40)])

    def test_manager_deletes_project(self):
        project = self.make_project()
        self.assertRedirects(self.client.post(reverse('project_delete', args=[project.pk])), reverse('project_list'))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_manager_deletes_mix(self):
        mix = MixRatio.objects.first()
        self.client.post(reverse('mix_delete', args=[mix.pk]))
        self.assertFalse(MixRatio.objects.filter(pk=mix.pk).exists())

    def test_used_material_cannot_be_deleted(self):
        sand = Material.objects.get(name='Sand')
        self.client.post(reverse('material_delete', args=[sand.pk]))
        self.assertTrue(Material.objects.filter(pk=sand.pk).exists())

    def test_unused_material_can_be_deleted_and_edited(self):
        lime = Material.objects.create(name='Lime', base_unit='bag')
        self.client.post(reverse('material_edit', args=[lime.pk]), {'name': 'Hydrated lime', 'is_active': ''})
        lime.refresh_from_db()
        self.assertEqual((lime.name, lime.is_active), ('Hydrated lime', False))
        self.client.post(reverse('material_delete', args=[lime.pk]))
        self.assertFalse(Material.objects.filter(pk=lime.pk).exists())

    def test_manager_withdraws_pending_price_only(self):
        pending = self.pending_price()
        approved = self.approve_price('Sand', '16.43')
        self.client.post(reverse('price_delete', args=[pending.pk]))
        self.assertEqual(self.client.post(reverse('price_delete', args=[approved.pk])).status_code, 404)
        self.assertFalse(MaterialPrice.objects.filter(pk=pending.pk).exists())
        self.assertTrue(MaterialPrice.objects.filter(pk=approved.pk).exists())

    def test_accountant_declines_with_corrected_price(self):
        pending = self.pending_price()
        accountant = self.as_role(User.Role.ACCOUNTANT)
        self.client.post(reverse('price_review', args=[pending.pk]), {'decision': 'declined', 'corrected_price': '16,43'})
        pending.refresh_from_db()
        self.assertEqual(pending.status, MaterialPrice.Status.DECLINED)
        replacement = MaterialPrice.objects.exclude(pk=pending.pk).get()
        self.assertEqual(replacement.price, Decimal('16.43'))
        self.assertEqual(replacement.status, MaterialPrice.Status.APPROVED)
        self.assertEqual((replacement.created_by, replacement.reviewed_by), (accountant, accountant))
        self.assertEqual(replacement.unit, 'wheelbarrow')

    def test_accountant_declines_without_correction(self):
        pending = self.pending_price()
        self.as_role(User.Role.ACCOUNTANT)
        self.client.post(reverse('price_review', args=[pending.pk]), {'decision': 'declined', 'corrected_price': ''})
        self.assertEqual(MaterialPrice.objects.count(), 1)
        pending.refresh_from_db()
        self.assertEqual(pending.status, MaterialPrice.Status.DECLINED)

    def test_invalid_corrected_price_changes_nothing(self):
        pending = self.pending_price()
        self.as_role(User.Role.ACCOUNTANT)
        self.client.post(reverse('price_review', args=[pending.pk]), {'decision': 'declined', 'corrected_price': '-5'})
        pending.refresh_from_db()
        self.assertEqual(pending.status, MaterialPrice.Status.PENDING)
        self.assertEqual(MaterialPrice.objects.count(), 1)


class ProjectCostTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.load_cape_town_prices()
        self.project = Project.objects.create(name='House', created_by=self.user)
        self.full = ProjectBlock.objects.create(project=self.project, block_type='F', quantity=70)
        self.half = ProjectBlock.objects.create(project=self.project, block_type='H', quantity=35)

    def project_price(self, material_name, price, project=None, status=MaterialPrice.Status.APPROVED):
        material = Material.objects.get(name=material_name)
        return MaterialPrice.objects.create(
            material=material, project=project or self.project, price=Decimal(price), unit=material.base_unit,
            status=status, created_by=self.user, reviewed_by=self.user, reviewed_at=timezone.now(),
        )

    def choose(self, block, mix_name):
        block.mix = MixRatio.objects.get(name=mix_name)
        block.save()

    def test_no_total_until_manager_chooses_every_mix(self):
        estimate = estimate_project(self.project)
        self.assertIsNone(estimate['total'])
        self.assertEqual(len(estimate['unchosen']), 2)
        self.assertTrue(all(line['selected'] is None for line in estimate['lines']))
        self.choose(self.full, 'Batch 2')
        estimate = estimate_project(self.project)
        self.assertIsNone(estimate['total'])
        self.assertEqual(estimate['unchosen'], [self.half])

    def test_project_total_uses_chosen_mixes(self):
        self.choose(self.full, 'Batch 4 (optimum)')
        self.choose(self.half, 'Batch 2')
        estimate = estimate_project(self.project)
        # 70 full with Batch 4: 3 batches x 161.36 = 484.08, plus 35 half with Batch 2: 1 x 177.79.
        self.assertEqual(estimate['total'], Decimal('661.87'))
        self.assertEqual(estimate['blocks'], 105)
        self.assertEqual([line['selected']['mix'].name for line in estimate['lines']], ['Batch 4 (optimum)', 'Batch 2'])
        # The cheapest is still flagged so the manager can compare.
        self.assertEqual(estimate['lines'][0]['best']['mix'].name, 'Batch 2')

    def test_project_price_overrides_default_only_for_that_project(self):
        other = Project.objects.create(name='Other', created_by=self.user)
        ProjectBlock.objects.create(project=other, block_type='F', quantity=22)
        self.project_price('Cement 50kg', '100.00')
        mine = latest_approved_prices(self.project)
        theirs = latest_approved_prices(other)
        cement = Material.objects.get(name='Cement 50kg').pk
        self.assertEqual(mine[cement].price, Decimal('100.00'))
        self.assertEqual(theirs[cement].price, Decimal('85.00'))

    def test_pending_project_price_is_not_used(self):
        self.project_price('Cement 50kg', '100.00', status=MaterialPrice.Status.PENDING)
        cement = Material.objects.get(name='Cement 50kg').pk
        self.assertEqual(latest_approved_prices(self.project)[cement].price, Decimal('85.00'))

    def test_project_price_is_not_a_default(self):
        self.project_price('Sand', '30.00')
        sand = Material.objects.get(name='Sand').pk
        self.assertEqual(latest_approved_prices()[sand].price, Decimal('16.43'))

    def test_manager_adds_project_price_as_pending(self):
        sand = Material.objects.get(name='Sand')
        response = self.client.post(reverse('project_price_add', args=[self.project.pk]), {
            'price-material': sand.pk, 'price-price': '20', 'price-price_unit': 'base', 'price-currency': 'zar',
        })
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]) + '#project-prices',
                             fetch_redirect_response=False)
        price = MaterialPrice.objects.get(project=self.project)
        self.assertEqual((price.status, price.currency), (MaterialPrice.Status.PENDING, 'ZAR'))

    def test_manager_chooses_and_changes_mix(self):
        batch4 = MixRatio.objects.get(name='Batch 4 (optimum)')
        batch3 = MixRatio.objects.get(name='Batch 3')
        url = reverse('project_choose_mix', args=[self.project.pk, self.full.pk])
        self.client.post(url, {'mix': batch4.pk})
        self.full.refresh_from_db()
        self.assertEqual(self.full.mix, batch4)
        self.client.post(url, {'mix': batch3.pk})
        self.full.refresh_from_db()
        self.assertEqual(self.full.mix, batch3)

    def test_cannot_choose_mix_for_other_block_type_or_inactive(self):
        half_only = MixRatio.objects.create(name='Half only', block_type='H', blocks_per_batch=40)
        inactive = MixRatio.objects.create(name='Old', block_type='B', blocks_per_batch=40, is_active=False)
        url = reverse('project_choose_mix', args=[self.project.pk, self.full.pk])
        self.assertEqual(self.client.post(url, {'mix': half_only.pk}).status_code, 404)
        self.assertEqual(self.client.post(url, {'mix': inactive.pk}).status_code, 404)
        self.assertEqual(self.client.post(url, {'mix': ''}).status_code, 404)

    def test_accountant_cannot_choose_mix_or_add_project_price(self):
        accountant = User.objects.create_user('acc', 'acc@example.com', 'S0me-strong-pass', role=User.Role.ACCOUNTANT)
        self.client.force_login(accountant)
        url = reverse('project_choose_mix', args=[self.project.pk, self.full.pk])
        self.assertEqual(self.client.post(url, {'mix': MixRatio.objects.first().pk}).status_code, 403)
        self.assertEqual(self.client.post(reverse('project_price_add', args=[self.project.pk]), {}).status_code, 403)

    def test_corrected_project_price_stays_on_project(self):
        pending = self.project_price('Sand', '40.00', status=MaterialPrice.Status.PENDING)
        accountant = User.objects.create_user('acc', 'acc@example.com', 'S0me-strong-pass', role=User.Role.ACCOUNTANT)
        self.client.force_login(accountant)
        next_url = reverse('project_detail', args=[self.project.pk])
        response = self.client.post(reverse('price_review', args=[pending.pk]), {
            'decision': 'declined', 'corrected_price': '18', 'next': next_url,
        })
        self.assertRedirects(response, next_url, fetch_redirect_response=False)
        replacement = MaterialPrice.objects.get(project=self.project, status=MaterialPrice.Status.APPROVED)
        self.assertEqual(replacement.price, Decimal('18'))

    def test_review_ignores_offsite_next(self):
        pending = self.project_price('Sand', '40.00', status=MaterialPrice.Status.PENDING)
        self.user.role = User.Role.ACCOUNTANT
        self.user.save()
        response = self.client.post(reverse('price_review', args=[pending.pk]), {
            'decision': 'approved', 'next': 'https://evil.example.com/',
        })
        self.assertRedirects(response, reverse('config'), fetch_redirect_response=False)

    def test_project_page_asks_manager_to_choose(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'to see the project total')
        self.assertContains(response, 'Choose this mix')
        self.assertNotContains(response, 'Materials for the whole project')

    def test_project_page_shows_total_and_project_price(self):
        self.project_price('Cement 50kg', '100.00')
        self.choose(self.full, 'Batch 2')
        self.choose(self.half, 'Batch 2')
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'Materials for the whole project')
        self.assertContains(response, 'This project')
