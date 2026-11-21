from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Material, MaterialPrice, MixRatio, Project, ProjectBlock
from .services import cost_mix, estimate_project, latest_approved_prices, mix_fits, pricing_data


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
    def cost(self, mix_name, **quantities):
        mix = MixRatio.objects.prefetch_related('ingredients__material').get(name=mix_name)
        return cost_mix(mix, quantities, latest_approved_prices())

    def material_row(self, result, name):
        return next(m for m in result['materials'] if m['material'].name == name)

    def test_cost_per_block_for_seeded_batches(self):
        self.load_cape_town_prices()
        # Batch 1: (3 x 16.43 + 85) / 22; Batch 2: (3 x 16.43 + 2 x 21.75 + 85) / 35
        self.assertEqual(self.cost('Batch 1', F=22)['cost_per_block'], Decimal('6.10'))
        self.assertEqual(self.cost('Batch 2', F=35)['cost_per_block'], Decimal('5.08'))
        self.assertEqual(self.cost('Batch 3', F=35)['cost_per_block'], Decimal('5.16'))
        self.assertEqual(self.cost('Batch 4 (optimum)', F=28)['cost_per_block'], Decimal('5.76'))

    def test_batches_round_up(self):
        self.load_cape_town_prices()
        result = self.cost('Batch 4 (optimum)', F=70)
        self.assertEqual(result['lines'][0]['batches'], 3)  # 70 / 28 -> 3 batches
        self.assertEqual(result['lines'][0]['blocks_produced'], 84)
        self.assertEqual(result['total'], Decimal('484.08'))  # 3 x 161.36

    def test_full_and_half_blocks_share_one_mixture(self):
        self.load_cape_town_prices()
        result = self.cost('Batch 2', F=70, H=35)
        self.assertEqual([(l['block_type'], l['batches']) for l in result['lines']], [('F', 2), ('H', 1)])
        self.assertEqual(result['total'], Decimal('533.37'))  # 3 batches x 177.79
        self.assertEqual(self.material_row(result, 'Sand')['quantity'], Decimal('9'))

    def test_quantities_and_prices_in_tonnes(self):
        self.load_cape_town_prices()
        result = self.cost('Batch 4 (optimum)', F=70)
        sand = self.material_row(result, 'Sand')
        cement = self.material_row(result, 'Cement 50kg')
        self.assertEqual(sand['tonnes'], Decimal('0.6'))  # 6 wheelbarrows x 0.1 t
        self.assertEqual(sand['price_per_tonne'], Decimal('164.30'))  # 16.43 / 0.1
        self.assertEqual(cement['tonnes'], Decimal('0.15'))  # 3 bags x 0.05 t
        self.assertEqual(cement['price_per_tonne'], Decimal('1700.00'))

    def test_price_per_tonne_is_converted_to_units(self):
        self.approve_price('Sand', '164.30', unit='t')
        self.approve_price('Cement 50kg', '85.00')
        self.assertEqual(self.cost('Batch 1', F=22)['total'], Decimal('134.29'))

    def test_material_without_weight_shows_units_only(self):
        self.load_cape_town_prices()
        Material.objects.filter(name='Sand').update(tonnes_per_unit=None)
        sand = self.material_row(self.cost('Batch 1', F=22), 'Sand')
        self.assertIsNone(sand['tonnes'])
        self.assertIsNone(sand['price_per_tonne'])

    def test_pending_price_is_not_used(self):
        self.approve_price('Sand', '16.43')
        MaterialPrice.objects.create(
            material=Material.objects.get(name='Cement 50kg'), price=Decimal('85'), unit='bag', created_by=self.user,
        )
        result = self.cost('Batch 1', F=22)
        self.assertIsNone(result['total'])
        self.assertEqual(result['missing'], ['Cement 50kg'])

    def test_cubic_metre_price_is_divided_by_16(self):
        self.approve_price('Sand', '262.88', unit='m3')  # 262.88 / 16 = 16.43
        self.approve_price('Cement 50kg', '85.00')
        self.assertEqual(self.cost('Batch 1', F=22)['total'], Decimal('134.29'))

    def test_mixture_must_fit_every_block_type(self):
        both = MixRatio.objects.get(name='Batch 1')
        half_only = MixRatio.objects.create(name='Half only', block_type='H', blocks_per_batch=40)
        self.assertTrue(mix_fits(both, ['F', 'H']))
        self.assertTrue(mix_fits(half_only, ['H']))
        self.assertFalse(mix_fits(half_only, ['F']))
        self.assertFalse(mix_fits(half_only, ['F', 'H']))

    def test_pricing_data_for_live_totals(self):
        self.load_cape_town_prices()
        data = pricing_data()
        sand = next(m for m in data['materials'] if m['name'] == 'Sand')
        self.assertEqual((sand['unit_price'], sand['tonnes_per_unit']), (16.43, 0.1))
        self.assertEqual(len(data['mixes']), 4)


class ViewTests(BaseTestCase):
    def project_post(self, **overrides):
        data = {
            'name': 'House', 'description': '', 'full_quantity': '500', 'half_quantity': '0',
            'mix': MixRatio.objects.get(name='Batch 2').pk,
        }
        data.update(overrides)
        return data

    def test_create_project_with_mixture(self):
        response = self.client.post(reverse('project_new'), self.project_post())
        project = Project.objects.get(name='House')
        self.assertRedirects(response, reverse('project_detail', args=[project.pk]))
        self.assertEqual(project.mix.name, 'Batch 2')
        self.assertEqual(list(project.blocks.values_list('block_type', 'quantity')), [('F', 500)])

    def test_create_project_requires_blocks_and_mixture(self):
        response = self.client.post(reverse('project_new'), self.project_post(full_quantity='0', mix=''))
        self.assertContains(response, 'Enter the number of full or half blocks.')
        self.assertContains(response, 'Choose a mixture.')
        self.assertFalse(Project.objects.exists())

    def test_create_project_rejects_mixture_for_other_block_type(self):
        half_only = MixRatio.objects.create(name='Half only', block_type='H', blocks_per_batch=40)
        response = self.client.post(reverse('project_new'), self.project_post(mix=half_only.pk))
        self.assertContains(response, 'Half only is only for half blocks.')
        self.assertFalse(Project.objects.exists())

    def test_create_page_has_no_strength_field_and_shows_mixtures(self):
        response = self.client.get(reverse('project_new'))
        self.assertNotContains(response, 'Required strength')
        for name in ('Batch 1', 'Batch 2', 'Batch 3', 'Batch 4 (optimum)'):
            self.assertContains(response, name)
        self.assertContains(response, 'id="pricing-data"')

    def test_project_page_shows_tonnes_and_total(self):
        self.load_cape_town_prices()
        project = Project.objects.create(name='House', created_by=self.user,
                                         mix=MixRatio.objects.get(name='Batch 4 (optimum)'))
        ProjectBlock.objects.create(project=project, block_type='F', quantity=70)
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(response, 'Batch 4 (optimum)')
        self.assertContains(response, 'R 484.08')
        self.assertContains(response, '0.60 t')
        self.assertContains(response, '6 wheelbarrows')
        self.assertContains(response, 'R 164.30')

    def mix_post(self, **quantities):
        data = {'name': 'Half mix', 'block_type': 'H', 'strength_mpa': '5', 'blocks_per_batch': '40', 'is_active': 'on'}
        for material in Material.objects.all():
            data[f'qty_{material.pk}'] = quantities.get(material.name, '')
        return data

    def test_create_mix_with_fixed_materials(self):
        response = self.client.post(reverse('mix_new'), self.mix_post(**{'Sand': '3', 'Cement 50kg': '1'}))
        self.assertRedirects(response, reverse('mixes'))
        mix = MixRatio.objects.get(name='Half mix')
        self.assertEqual(
            {(i.material.name, i.quantity, i.unit) for i in mix.ingredients.select_related('material')},
            {('Sand', Decimal('3'), 'wheelbarrow'), ('Cement 50kg', Decimal('1'), 'bag')},
        )

    def test_mix_form_shows_one_row_per_material(self):
        response = self.client.get(reverse('mix_new'))
        for material in Material.objects.all():
            self.assertContains(response, f'name="qty_{material.pk}"')
        self.assertNotContains(response, 'ingredients-TOTAL_FORMS')

    def test_editing_mix_updates_and_removes_quantities(self):
        mix = MixRatio.objects.get(name='Batch 2')
        data = self.mix_post(**{'Sand': '4', 'Cement 50kg': '1'})
        data.update({'name': 'Batch 2', 'block_type': 'B', 'blocks_per_batch': '35'})
        self.client.post(reverse('mix_edit', args=[mix.pk]), data)
        quantities = {i.material.name: i.quantity for i in mix.ingredients.select_related('material')}
        self.assertEqual(quantities, {'Sand': Decimal('4'), 'Cement 50kg': Decimal('1')})

    def test_mix_needs_at_least_one_quantity(self):
        response = self.client.post(reverse('mix_new'), self.mix_post())
        self.assertContains(response, 'Enter a quantity for at least one material.')
        self.assertFalse(MixRatio.objects.filter(name='Half mix').exists())

    def test_add_price_then_history_lists_it(self):
        sand = Material.objects.get(name='Sand')
        response = self.client.post(reverse('price_add'), {
            'price-material': sand.pk, 'price-price': '150', 'price-price_unit': 'base', 'price-currency': 'ZAR',
        }, follow=True)
        self.assertRedirects(response, reverse('materials'))
        self.assertContains(response, 'sent for approval')
        self.assertContains(response, '1 price waiting for approval.')
        history = self.client.get(reverse('price_history'))
        self.assertContains(history, 'R 150.00 <span class="muted small">per wheelbarrow</span>', html=False)

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
        project = Project.objects.create(name=f'{status} job', created_by=self.user, status=status,
                                         mix=MixRatio.objects.get(name='Batch 2'))
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
        for name in ('mixes', 'materials', 'price_history'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.as_role(User.Role.CREATOR)
        for name in ('mixes', 'materials', 'price_history', 'config'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)

    def test_manager_edits_project_name_and_blocks(self):
        project = self.make_project()
        response = self.client.post(reverse('project_edit', args=[project.pk]), {
            'name': 'Renamed', 'description': '', 'status': 'completed',
            'full_quantity': '0', 'half_quantity': '40', 'mix': MixRatio.objects.get(name='Batch 3').pk,
        })
        self.assertRedirects(response, reverse('project_detail', args=[project.pk]))
        project.refresh_from_db()
        # Status is ignored here; it only changes through the status form.
        self.assertEqual((project.name, project.status, project.mix.name), ('Renamed', 'draft', 'Batch 3'))
        self.assertEqual(list(project.blocks.values_list('block_type', 'quantity')), [('H', 40)])

    def test_manager_deletes_project(self):
        project = self.make_project()
        self.assertRedirects(self.client.post(reverse('project_delete', args=[project.pk])), reverse('project_list'))
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_manager_deletes_mix(self):
        mix = MixRatio.objects.get(name='Batch 1')
        self.client.post(reverse('mix_delete', args=[mix.pk]))
        self.assertFalse(MixRatio.objects.filter(pk=mix.pk).exists())

    def test_mix_used_by_a_project_cannot_be_deleted(self):
        self.make_project()
        mix = MixRatio.objects.get(name='Batch 2')
        self.client.post(reverse('mix_delete', args=[mix.pk]))
        self.assertTrue(MixRatio.objects.filter(pk=mix.pk).exists())

    def test_material_weight_can_be_edited(self):
        sand = Material.objects.get(name='Sand')
        self.client.post(reverse('material_edit', args=[sand.pk]), {'name': 'Sand', 'weight_kg': '110', 'is_active': 'on'})
        sand.refresh_from_db()
        self.assertEqual(sand.tonnes_per_unit, Decimal('0.11'))

    def test_used_material_cannot_be_deleted(self):
        sand = Material.objects.get(name='Sand')
        self.client.post(reverse('material_delete', args=[sand.pk]))
        self.assertTrue(Material.objects.filter(pk=sand.pk).exists())

    def test_unused_material_can_be_deleted_and_edited(self):
        lime = Material.objects.create(name='Lime', base_unit='bag')
        self.client.post(reverse('material_edit', args=[lime.pk]), {'name': 'Hydrated lime', 'weight_kg': '25', 'is_active': ''})
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


class ProjectPriceTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.load_cape_town_prices()
        self.project = Project.objects.create(name='House', created_by=self.user,
                                              mix=MixRatio.objects.get(name='Batch 4 (optimum)'))
        ProjectBlock.objects.create(project=self.project, block_type='F', quantity=70)
        self.sand = Material.objects.get(name='Sand')
        self.set_url = reverse('project_prices_save', args=[self.project.pk])
        self.reset_url = reverse('project_price_reset', args=[self.project.pk, self.sand.pk])

    def test_project_has_no_total_without_mixture(self):
        project = Project.objects.create(name='No mix', created_by=self.user)
        ProjectBlock.objects.create(project=project, block_type='F', quantity=70)
        estimate = estimate_project(project)
        self.assertIsNone(estimate['total'])
        self.assertContains(self.client.get(reverse('project_detail', args=[project.pk])), 'No mixture chosen yet.')

    def test_manager_sets_project_price_per_tonne(self):
        response = self.client.post(self.set_url, {f'price_{self.sand.pk}': '200'})
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]) + '#materials',
                             fetch_redirect_response=False)
        price = MaterialPrice.objects.get(project=self.project)
        self.assertEqual((price.price, price.unit, price.status), (Decimal('200'), 't', 'approved'))
        # 6 wheelbarrows x 0.1 t x 200 = 120.00 instead of 98.58 for sand.
        self.assertEqual(estimate_project(self.project)['total'], Decimal('505.50'))

    def test_project_price_does_not_change_other_projects_or_defaults(self):
        self.client.post(self.set_url, {f'price_{self.sand.pk}': '200'})
        other = Project.objects.create(name='Other', created_by=self.user, mix=self.project.mix)
        ProjectBlock.objects.create(project=other, block_type='F', quantity=70)
        self.assertEqual(estimate_project(other)['total'], Decimal('484.08'))
        self.assertEqual(latest_approved_prices()[self.sand.pk].price, Decimal('16.43'))

    def test_newest_project_price_wins_and_reset_restores_default(self):
        self.client.post(self.set_url, {f'price_{self.sand.pk}': '200'})
        self.client.post(self.set_url, {f'price_{self.sand.pk}': '180'})
        self.assertEqual(latest_approved_prices(self.project)[self.sand.pk].price, Decimal('180'))
        self.client.post(self.reset_url)
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())
        self.assertEqual(estimate_project(self.project)['total'], Decimal('484.08'))

    def test_invalid_project_price_is_rejected(self):
        self.client.post(self.set_url, {f'price_{self.sand.pk}': '-5'})
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())

    def test_material_without_weight_is_priced_per_unit(self):
        Material.objects.filter(pk=self.sand.pk).update(tonnes_per_unit=None)
        self.client.post(self.set_url, {f'price_{self.sand.pk}': '20'})
        self.assertEqual(MaterialPrice.objects.get(project=self.project).unit, 'wheelbarrow')

    def test_only_manager_sets_project_prices(self):
        accountant = User.objects.create_user('acc', 'acc@example.com', 'S0me-strong-pass', role=User.Role.ACCOUNTANT)
        self.client.force_login(accountant)
        self.assertEqual(self.client.post(self.set_url, {f'price_{self.sand.pk}': '200'}).status_code, 403)
        self.assertEqual(self.client.post(self.reset_url).status_code, 403)

    def test_project_page_shows_price_editor_to_manager(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'Save all prices')
        self.assertContains(response, self.set_url)

    def test_review_ignores_offsite_next(self):
        pending = MaterialPrice.objects.create(material=self.sand, price=Decimal('40'), unit='wheelbarrow',
                                               created_by=self.user)
        self.user.role = User.Role.ACCOUNTANT
        self.user.save()
        response = self.client.post(reverse('price_review', args=[pending.pk]), {
            'decision': 'approved', 'next': 'https://evil.example.com/',
        })
        self.assertRedirects(response, reverse('price_history'), fetch_redirect_response=False)


class ProjectStatusTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.load_cape_town_prices()
        self.project = Project.objects.create(name='House', created_by=self.user)
        self.block = ProjectBlock.objects.create(project=self.project, block_type='F', quantity=70)
        self.url = reverse('project_status', args=[self.project.pk])
        self.review_url = reverse('project_review', args=[self.project.pk])
        self.detail = reverse('project_detail', args=[self.project.pk])
        self.accountant = User.objects.create_user(
            'acc', 'acc@example.com', 'S0me-strong-pass', full_name='Accountant', role=User.Role.ACCOUNTANT,
        )

    def choose_mix(self):
        self.project.mix = MixRatio.objects.get(name='Batch 4 (optimum)')
        self.project.save()

    def status(self):
        self.project.refresh_from_db()
        return self.project.status

    def send_for_approval(self):
        self.choose_mix()
        self.client.post(self.url, {'status': 'pending'})

    def approve(self):
        self.send_for_approval()
        self.client.force_login(self.accountant)
        self.client.post(self.review_url, {'decision': 'approved'})
        self.client.force_login(self.user)

    def complete(self):
        self.approve()
        return self.client.post(self.url, {'status': 'completed'})

    # ----- manager steps -----

    def test_new_project_starts_as_draft(self):
        self.assertEqual(self.status(), 'draft')
        self.assertEqual(self.project.manager_next_status, 'pending')

    def test_draft_to_pending_needs_a_mixture(self):
        self.client.post(self.url, {'status': 'pending'})
        self.assertEqual(self.status(), 'draft')
        self.send_for_approval()
        self.assertEqual(self.status(), 'pending')

    def test_pending_back_to_draft(self):
        self.send_for_approval()
        self.client.post(self.url, {'status': 'draft'})
        self.assertEqual(self.status(), 'draft')

    def test_manager_cannot_skip_steps(self):
        self.choose_mix()
        for status in ('approved', 'completed', 'declined', 'draft'):
            self.client.post(self.url, {'status': status})
            self.assertEqual(self.status(), 'draft', status)
        self.client.post(self.url, {'status': 'pending'})
        for status in ('approved', 'completed', 'pending'):
            self.client.post(self.url, {'status': status})
            self.assertEqual(self.status(), 'pending', status)

    def test_manager_cannot_approve(self):
        self.send_for_approval()
        self.client.post(self.review_url, {'decision': 'approved'})
        self.assertEqual(self.status(), 'pending')

    def test_status_form_shows_only_the_next_step(self):
        self.choose_mix()
        response = self.client.get(self.detail)
        self.assertContains(response, 'Send for approval')
        self.assertNotContains(response, 'Back to draft')
        self.assertNotContains(response, 'Mark completed')
        self.client.post(self.url, {'status': 'pending'})
        response = self.client.get(self.detail)
        self.assertContains(response, 'Back to draft')
        self.assertNotContains(response, 'value="pending"')

    # ----- pending lock -----

    def test_pending_project_only_allows_price_changes(self):
        self.send_for_approval()
        mix = MixRatio.objects.get(name='Batch 2')
        for response in (
            self.client.get(reverse('project_edit', args=[self.project.pk])),
            self.client.post(reverse('project_edit', args=[self.project.pk]),
                             {'name': 'X', 'full_quantity': '1', 'half_quantity': '0', 'mix': mix.pk}),
            self.client.post(reverse('project_delete', args=[self.project.pk])),
        ):
            self.assertRedirects(response, self.detail)
        self.project.refresh_from_db()
        self.assertEqual((self.project.name, self.project.mix.name), ('House', 'Batch 4 (optimum)'))

        sand = Material.objects.get(name='Sand')
        self.client.post(reverse('project_prices_save', args=[self.project.pk]), {f'price_{sand.pk}': '200'})
        self.assertTrue(MaterialPrice.objects.filter(project=self.project).exists())
        self.client.post(reverse('project_price_reset', args=[self.project.pk, sand.pk]))
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())

    def test_pending_page_hides_edit_controls_but_keeps_price_editor(self):
        self.send_for_approval()
        response = self.client.get(self.detail)
        self.assertNotContains(response, 'Edit project')
        self.assertNotContains(response, 'Change mixture')
        self.assertContains(response, 'Save all prices')

    # ----- accountant decisions -----

    def test_accountant_approves_pending_project(self):
        self.approve()
        self.assertEqual(self.status(), 'approved')
        approval = self.project.approvals.get()
        self.assertEqual((approval.decision, approval.reviewed_by), ('approved', self.accountant))

    def test_accountant_declines_back_to_draft_with_comment(self):
        self.send_for_approval()
        self.client.force_login(self.accountant)
        self.client.post(self.review_url, {'decision': 'declined', 'comments': ''})
        self.assertEqual(self.status(), 'pending')  # a comment is required
        self.client.post(self.review_url, {'decision': 'declined', 'comments': 'Use Batch 2 instead.'})
        self.assertEqual(self.status(), 'draft')
        self.assertEqual(self.project.approvals.get().comments, 'Use Batch 2 instead.')
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.detail), 'Use Batch 2 instead.')

    def test_cannot_send_for_approval_without_every_price(self):
        MaterialPrice.objects.filter(material__name='Sand').delete()
        self.send_for_approval()
        self.assertEqual(self.status(), 'draft')
        response = self.client.get(self.detail)
        self.assertContains(response, 'Set a price for Sand first.')
        self.client.post(reverse('project_prices_save', args=[self.project.pk]),
                         {f'price_{Material.objects.get(name="Sand").pk}': '164.30'})
        self.client.post(self.url, {'status': 'pending'})
        self.assertEqual(self.status(), 'pending')

    def test_accountant_cannot_approve_if_a_price_disappeared(self):
        self.send_for_approval()
        MaterialPrice.objects.filter(material__name='Sand').delete()
        self.client.force_login(self.accountant)
        self.client.post(self.review_url, {'decision': 'approved'})
        self.assertEqual(self.status(), 'pending')

    def test_review_only_for_pending_projects(self):
        self.choose_mix()
        self.client.force_login(self.accountant)
        self.client.post(self.review_url, {'decision': 'approved'})
        self.assertEqual(self.status(), 'draft')

    def test_creator_cannot_review(self):
        self.send_for_approval()
        creator = User.objects.create_user('cre', 'cre@example.com', 'S0me-strong-pass', role=User.Role.CREATOR)
        self.client.force_login(creator)
        self.assertEqual(self.client.post(self.review_url, {'decision': 'approved'}).status_code, 403)

    def test_project_list_tells_accountant_about_pending_projects(self):
        self.send_for_approval()
        self.client.force_login(self.accountant)
        self.assertContains(self.client.get(reverse('project_list')), '1 project waiting for your approval')

    # ----- approved and completed -----

    def test_approved_project_cannot_be_edited_or_priced(self):
        self.approve()
        sand = Material.objects.get(name='Sand')
        self.assertRedirects(self.client.get(reverse('project_edit', args=[self.project.pk])), self.detail)
        self.client.post(reverse('project_prices_save', args=[self.project.pk]), {f'price_{sand.pk}': '200'})
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())
        self.assertNotContains(self.client.get(self.detail), 'Save all prices')
        self.client.post(self.url, {'status': 'draft'})
        self.assertEqual(self.status(), 'approved')

    def test_completing_saves_costs_as_history(self):
        self.complete()
        self.assertEqual(self.status(), 'completed')
        self.assertIsNotNone(self.project.completed_at)
        estimate = self.project.estimates.get()
        # 70 full with Batch 4: 3 batches x (2 x 16.43 + 2 x 21.75 + 85).
        self.assertEqual(estimate.total_material_cost, Decimal('484.08'))
        self.assertEqual(estimate.breakdown[0]['mix'], 'Batch 4 (optimum)')
        per_batch = {i['material']: Decimal(i['quantity']) for i in estimate.breakdown[0]['ingredients']}
        self.assertEqual(per_batch, {'Sand': 2, 'Stone 13mm': 2, 'Cement 50kg': 1})
        sand = estimate.materials.get(material__name='Sand')
        self.assertEqual((sand.quantity_required, sand.unit_price_snapshot), (Decimal('6'), Decimal('16.43')))

    def test_history_ignores_later_price_changes(self):
        self.complete()
        self.approve_price('Cement 50kg', '200.00')
        response = self.client.get(self.detail)
        self.assertContains(response, 'R 484.08')
        self.assertContains(response, 'Later price or mix changes')

    def test_completed_project_is_locked(self):
        self.complete()
        for status in ('draft', 'pending', 'approved'):
            self.client.post(self.url, {'status': status})
        self.assertEqual(self.status(), 'completed')
        self.assertRedirects(self.client.post(reverse('project_delete', args=[self.project.pk])), self.detail)
        response = self.client.get(self.detail)
        self.assertNotContains(response, 'Edit project')
        self.assertNotContains(response, 'Mark completed')
        self.assertContains(response, 'kept as history')


class CurrencyCaseTests(BaseTestCase):
    def test_currency_case_does_not_split_the_total(self):
        self.approve_price('Sand', '16.43')
        price = self.approve_price('Cement 50kg', '85.00')
        MaterialPrice.objects.filter(pk=price.pk).update(currency='Zar')
        mix = MixRatio.objects.prefetch_related('ingredients__material').get(name='Batch 1')
        result = cost_mix(mix, {'F': 22}, latest_approved_prices())
        self.assertEqual((result['total'], result['currency']), (Decimal('134.29'), 'ZAR'))


class QuantityHintTests(BaseTestCase):
    def test_block_counts_start_empty_with_zero_hint(self):
        response = self.client.get(reverse('project_new'))
        self.assertContains(response, 'placeholder="0"', count=2)
        self.assertNotContains(response, 'name="full_quantity" id="id_full_quantity"\n         placeholder="0" value=')

    def test_edit_shows_saved_count_and_leaves_missing_type_empty(self):
        project = Project.objects.create(name='House', created_by=self.user, mix=MixRatio.objects.get(name='Batch 2'))
        ProjectBlock.objects.create(project=project, block_type='F', quantity=500)
        html = self.client.get(reverse('project_edit', args=[project.pk])).content.decode()
        self.assertIn('value="500"', html)
        self.assertNotIn('value="0"', html)


class SplitPagesTests(BaseTestCase):
    def test_old_config_address_redirects_to_mixes(self):
        self.assertRedirects(self.client.get(reverse('config')), reverse('mixes'))

    def test_each_page_shows_its_own_content(self):
        mixes = self.client.get(reverse('mixes'))
        self.assertContains(mixes, 'Batch 4 (optimum)')
        self.assertNotContains(mixes, 'Add a material')
        materials = self.client.get(reverse('materials'))
        self.assertContains(materials, 'Stone 13mm')
        self.assertContains(materials, 'Add a default price')
        self.assertNotContains(materials, 'Batch 4 (optimum)')
        history = self.client.get(reverse('price_history'))
        self.assertContains(history, 'Price history')
        self.assertNotContains(history, 'Add a material')

    def test_navigation_links_to_the_three_pages(self):
        response = self.client.get(reverse('project_list'))
        for name in ('mixes', 'materials', 'price_history'):
            self.assertContains(response, f'href="{reverse(name)}"')

    def test_history_filters_by_status_and_lists_pending_first(self):
        sand = Material.objects.get(name='Sand')
        self.approve_price('Sand', '16.43')
        MaterialPrice.objects.create(material=sand, price=Decimal('20'), unit='wheelbarrow', created_by=self.user)
        response = self.client.get(reverse('price_history'))
        prices = list(response.context['prices'])
        self.assertEqual(prices[0].status, 'pending')
        pending = self.client.get(reverse('price_history'), {'status': 'pending'})
        self.assertEqual([p.status for p in pending.context['prices']], ['pending'])

    def test_review_from_history_returns_to_history(self):
        sand = Material.objects.get(name='Sand')
        price = MaterialPrice.objects.create(material=sand, price=Decimal('20'), unit='wheelbarrow', created_by=self.user)
        self.user.role = User.Role.ACCOUNTANT
        self.user.save()
        next_url = reverse('price_history') + '?status=pending'
        response = self.client.post(reverse('price_review', args=[price.pk]), {'decision': 'approved', 'next': next_url})
        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_mix_and_material_saves_return_to_their_pages(self):
        lime = Material.objects.create(name='Lime', base_unit='bag')
        response = self.client.post(reverse('material_edit', args=[lime.pk]), {'name': 'Lime', 'weight_kg': '25', 'is_active': 'on'})
        self.assertRedirects(response, reverse('materials'))


class MaterialFormTests(BaseTestCase):
    def add_material(self, **data):
        post = {'material-name': 'Lime', 'material-base_unit': 'bag', 'material-weight_kg': '25'}
        post.update({f'material-{k}': v for k, v in data.items()})
        return self.client.post(reverse('material_add'), post)

    def add_price(self, material, basis, price='100', currency='zar'):
        return self.client.post(reverse('price_add'), {
            'price-material': material.pk, 'price-price_unit': basis, 'price-price': price, 'price-currency': currency,
        })

    def test_add_bagged_material_with_weight_in_kg(self):
        self.assertRedirects(self.add_material(), reverse('materials'))
        lime = Material.objects.get(name='Lime')
        self.assertEqual((lime.base_unit, lime.tonnes_per_unit), ('bag', Decimal('0.025')))

    def test_material_needs_a_weight_unless_bought_by_the_tonne(self):
        response = self.add_material(weight_kg='')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Enter how many kg one bag weighs', status_code=400)
        self.assertFalse(Material.objects.filter(name='Lime').exists())
        self.assertRedirects(self.add_material(name='Gravel', base_unit='tonne', weight_kg=''), reverse('materials'))
        self.assertEqual(Material.objects.get(name='Gravel').tonnes_per_unit, Decimal('1'))

    def test_unit_must_be_one_of_the_choices(self):
        response = self.add_material(base_unit='bucket')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Material.objects.filter(name='Lime').exists())

    def test_cement_can_be_priced_per_bag_or_tonne_but_not_m3(self):
        cement = Material.objects.get(name='Cement 50kg')
        response = self.add_price(cement, 'm3')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Cement 50kg can be priced per tonne, bag.', status_code=400)
        self.assertRedirects(self.add_price(cement, 'base', '85'), reverse('materials'))
        self.assertRedirects(self.add_price(cement, 't', '1700'), reverse('materials'))
        units = list(MaterialPrice.objects.filter(material=cement).order_by('created_at').values_list('unit', 'currency'))
        self.assertEqual(units, [('bag', 'ZAR'), ('t', 'ZAR')])

    def test_sand_can_be_priced_per_m3(self):
        sand = Material.objects.get(name='Sand')
        self.assertRedirects(self.add_price(sand, 'm3', '262.88'), reverse('materials'))
        self.assertEqual(MaterialPrice.objects.get(material=sand).unit, 'm3')

    def test_invalid_price_form_keeps_what_was_typed(self):
        cement = Material.objects.get(name='Cement 50kg')
        response = self.add_price(cement, 'm3', '123.45')
        self.assertContains(response, 'value="123.45"', status_code=400)

    def test_materials_page_shows_weight_in_kg_and_price_options(self):
        response = self.client.get(reverse('materials'))
        self.assertContains(response, '50 kg per bag')
        self.assertContains(response, '100 kg per wheelbarrow')
        self.assertContains(response, 'id="price-bases"')
        self.assertContains(response, 'Bought and measured by')

    def test_edit_material_weight_in_kg(self):
        cement = Material.objects.get(name='Cement 50kg')
        response = self.client.get(reverse('material_edit', args=[cement.pk]))
        self.assertContains(response, 'Weight of one bag (kg)')
        self.assertContains(response, 'value="50"')


class SaveAllPricesTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.load_cape_town_prices()
        self.project = Project.objects.create(name='House', created_by=self.user,
                                              mix=MixRatio.objects.get(name='Batch 4 (optimum)'))
        ProjectBlock.objects.create(project=self.project, block_type='F', quantity=70)
        self.url = reverse('project_prices_save', args=[self.project.pk])
        self.ids = {m.name: m.pk for m in Material.objects.all()}

    def post(self, **prices):
        return self.client.post(self.url, {f'price_{self.ids[name]}': value for name, value in prices.items()})

    def test_saves_every_changed_price_at_once(self):
        response = self.post(**{'Sand': '200', 'Stone 13mm': '241.67', 'Cement 50kg': '1800'})
        self.assertRedirects(response, reverse('project_detail', args=[self.project.pk]) + '#materials',
                             fetch_redirect_response=False)
        saved = dict(MaterialPrice.objects.filter(project=self.project).values_list('material__name', 'price'))
        # Stone is unchanged (21.75 / 0.09 = 241.67 per tonne), so only two prices are saved.
        self.assertEqual(saved, {'Sand': Decimal('200'), 'Cement 50kg': Decimal('1800')})

    def test_invalid_price_saves_nothing_and_keeps_what_was_typed(self):
        response = self.post(**{'Sand': '200', 'Cement 50kg': 'abc'})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'Nothing was saved.', status_code=400)
        self.assertContains(response, 'value="200"', status_code=400)
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())

    def test_nothing_changed(self):
        response = self.post(**{'Sand': '164.30'})
        self.assertFalse(MaterialPrice.objects.filter(project=self.project).exists())
        self.assertEqual(response.status_code, 302)

    def test_one_form_with_save_all_button(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'id="prices-form"')
        self.assertContains(response, 'Save all prices')
        for pk in self.ids.values():
            self.assertContains(response, f'name="price_{pk}"')


class CreatorPriceVisibilityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.load_cape_town_prices()
        self.project = Project.objects.create(name='House', created_by=self.user, status=Project.Status.APPROVED,
                                              mix=MixRatio.objects.get(name='Batch 4 (optimum)'))
        ProjectBlock.objects.create(project=self.project, block_type='F', quantity=70)
        self.creator = User.objects.create_user('cre', 'cre@example.com', 'S0me-strong-pass', role=User.Role.CREATOR)

    def test_creator_sees_materials_without_prices(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'Materials needed')
        self.assertContains(response, '0.60 t')
        self.assertNotContains(response, 'R 484.08')
        self.assertNotContains(response, 'R 164.30')
        self.assertNotContains(response, '/ t')

    def test_creator_sees_completed_history_without_prices(self):
        from .services import save_estimate
        save_estimate(self.project, self.user)
        Project.objects.filter(pk=self.project.pk).update(status=Project.Status.COMPLETED)
        self.client.force_login(self.creator)
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'Materials used')
        self.assertContains(response, '0.60 t')
        self.assertNotContains(response, 'R 484.08')

    def test_manager_still_sees_prices(self):
        response = self.client.get(reverse('project_detail', args=[self.project.pk]))
        self.assertContains(response, 'R 484.08')
