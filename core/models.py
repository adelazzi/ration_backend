from django.conf import settings
from django.db import models
from django.db.models import Q


class BlockType(models.TextChoices):
    HALF = 'H', 'Half'
    FULL = 'F', 'Full'


class MixBlockType(models.TextChoices):
    BOTH = 'B', 'Both (half and full)'
    HALF = 'H', 'Half'
    FULL = 'F', 'Full'


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DECLINED = 'declined', 'Declined'
        COMPLETED = 'completed', 'Completed'

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return self.name

    @property
    def is_locked(self):
        """Completed projects are history: their costs are saved and they can't be changed."""
        return self.status == self.Status.COMPLETED

    @property
    def final_estimate(self):
        return self.estimates.order_by('-version').first() if self.is_locked else None


class ProjectBlock(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=1, choices=BlockType.choices)
    quantity = models.PositiveIntegerField()
    required_strength_mpa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    # The mix chosen for this line; empty means "use the cheapest suitable mix".
    mix = models.ForeignKey('MixRatio', on_delete=models.SET_NULL, null=True, blank=True, related_name='project_blocks')

    class Meta:
        db_table = 'project_blocks'
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name='project_block_quantity_gt_0'),
            models.CheckConstraint(condition=Q(block_type__in=['H', 'F']), name='project_block_type_h_or_f'),
        ]

    def __str__(self):
        return f'{self.project} – {self.get_block_type_display()} x{self.quantity}'


class Material(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_unit = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'materials'

    def __str__(self):
        return self.name


class MixRatio(models.Model):
    name = models.CharField(max_length=100)
    # Business rule 4: the yield is defined for the block types the mix applies to.
    block_type = models.CharField(max_length=1, choices=MixBlockType.choices, default=MixBlockType.BOTH)
    strength_mpa = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    blocks_per_batch = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'mix_ratios'
        constraints = [
            models.CheckConstraint(condition=Q(blocks_per_batch__gt=0), name='mix_blocks_per_batch_gt_0'),
            models.CheckConstraint(condition=Q(block_type__in=['B', 'H', 'F']), name='mix_block_type_b_h_or_f'),
        ]

    def __str__(self):
        return self.name


class MixIngredient(models.Model):
    mix = models.ForeignKey(MixRatio, on_delete=models.CASCADE, related_name='ingredients')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='mix_ingredients')
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit = models.CharField(max_length=20)

    class Meta:
        db_table = 'mix_ingredients'
        constraints = [
            models.UniqueConstraint(fields=['mix', 'material'], name='unique_mix_material'),
        ]

    def __str__(self):
        return f'{self.mix}: {self.quantity} {self.unit} {self.material}'


class MaterialPrice(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DECLINED = 'declined', 'Declined'

    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='prices')
    # Empty for a default price; set when the price only applies to one project.
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, null=True, blank=True, related_name='material_prices'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=20)
    currency = models.CharField(max_length=3, default='ZAR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='prices_entered'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name='prices_reviewed',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'material_prices'

    def __str__(self):
        return f'{self.material} {self.price} {self.currency}/{self.unit} ({self.status})'


class ProjectEstimate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='estimates')
    version = models.PositiveIntegerField()
    total_material_cost = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='estimates'
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    # Snapshot of each block line at calculation time: block type, quantity, mix, batches, cost.
    breakdown = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'project_estimates'
        constraints = [
            models.UniqueConstraint(fields=['project', 'version'], name='unique_project_estimate_version'),
        ]

    def __str__(self):
        return f'{self.project} v{self.version}'


class EstimateMaterial(models.Model):
    estimate = models.ForeignKey(ProjectEstimate, on_delete=models.CASCADE, related_name='materials')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='estimate_lines')
    quantity_required = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=20)
    # Business rule 2: keep the price used at calculation time.
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = 'estimate_materials'

    def __str__(self):
        return f'{self.estimate}: {self.material}'


class ProjectApproval(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Approved'
        DECLINED = 'declined', 'Declined'

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name='approvals')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approvals'
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    comments = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'project_approvals'

    def __str__(self):
        return f'{self.project}: {self.decision}'
