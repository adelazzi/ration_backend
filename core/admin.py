from django.contrib import admin

from .models import (
    EstimateMaterial, Material, MaterialPrice, MixIngredient, MixRatio,
    Project, ProjectApproval, ProjectBlock, ProjectEstimate,
)


class ProjectBlockInline(admin.TabularInline):
    model = ProjectBlock
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_by', 'created_at')
    list_filter = ('status',)
    inlines = [ProjectBlockInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_unit', 'is_active')


class MixIngredientInline(admin.TabularInline):
    model = MixIngredient
    extra = 0


@admin.register(MixRatio)
class MixRatioAdmin(admin.ModelAdmin):
    list_display = ('name', 'block_type', 'strength_mpa', 'blocks_per_batch', 'is_active')
    inlines = [MixIngredientInline]


@admin.register(MaterialPrice)
class MaterialPriceAdmin(admin.ModelAdmin):
    list_display = ('material', 'price', 'unit', 'currency', 'status', 'created_by', 'reviewed_by')
    list_filter = ('status',)


class EstimateMaterialInline(admin.TabularInline):
    model = EstimateMaterial
    extra = 0


@admin.register(ProjectEstimate)
class ProjectEstimateAdmin(admin.ModelAdmin):
    list_display = ('project', 'version', 'total_material_cost', 'currency', 'calculated_at')
    inlines = [EstimateMaterialInline]


@admin.register(ProjectApproval)
class ProjectApprovalAdmin(admin.ModelAdmin):
    list_display = ('project', 'decision', 'reviewed_by', 'reviewed_at')
