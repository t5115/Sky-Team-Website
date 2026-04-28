from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from departments.models import Department
from teams.models import Team

from .forms import TeamResourceForm
from .models import TeamResource


RESOURCE_PAGE_CONFIG = {
    TeamResource.ResourceType.SERVICE: {
        'title': 'Services',
        'singular': 'Service',
        'icon': 'bi-box-seam',
        'description': 'Services owned or maintained by Sky teams.',
        'list_url_name': 'resources:service_list',
    },
    TeamResource.ResourceType.REPOSITORY: {
        'title': 'Repositories',
        'singular': 'Repository',
        'icon': 'bi-git',
        'description': 'Code repositories owned or maintained by Sky teams.',
        'list_url_name': 'resources:repository_list',
    },
    TeamResource.ResourceType.CONTACT_CHANNEL: {
        'title': 'Contact Channels',
        'singular': 'Contact Channel',
        'icon': 'bi-chat-left-text',
        'description': 'Team contact channels such as Teams, Slack, email, or support links.',
        'list_url_name': 'resources:contact_channel_list',
    },
}


def superuser_required(user):
    """Only superusers are allowed to create, edit, or change resource status."""
    return user.is_authenticated and user.is_superuser


def _get_resource_config(resource_type):
    """
    Return page configuration for a resource type or raise 404 through get_object_or_404 style logic.
    """
    return RESOURCE_PAGE_CONFIG.get(resource_type)


def _resource_list(request, resource_type):
    """
    Shared list view used by services, repositories, and contact channels.

    The data model is shared, but the sidebar separates the feature into three
    user-friendly pages. This function keeps the filtering logic in one place so
    the three pages behave consistently.
    """
    config = _get_resource_config(resource_type)
    if config is None:
        messages.error(request, 'Unknown resource type.')
        return redirect('core:home')

    search_query = request.GET.get('search', '').strip()
    team_id = request.GET.get('team', '').strip()
    department_id = request.GET.get('department', '').strip()
    status_filter = request.GET.get('status', 'active').strip()

    resources = (
        TeamResource.objects
        .filter(resource_type=resource_type)
        .select_related('team', 'team__department', 'team__team_leader')
    )

    if search_query:
        resources = resources.filter(
            models.Q(name__icontains=search_query)
            | models.Q(description__icontains=search_query)
            | models.Q(url__icontains=search_query)
            | models.Q(contact_detail__icontains=search_query)
            | models.Q(team__name__icontains=search_query)
        ).distinct()

    if team_id:
        resources = resources.filter(team_id=team_id)

    if department_id:
        resources = resources.filter(team__department_id=department_id)

    if status_filter == 'active':
        resources = resources.filter(is_active=True)
    elif status_filter == 'inactive':
        resources = resources.filter(is_active=False)

    context = {
        'resources': resources,
        'config': config,
        'resource_type': resource_type,
        'search_query': search_query,
        'team_id': team_id,
        'department_id': department_id,
        'status_filter': status_filter,
        'teams': Team.objects.select_related('department').order_by('name'),
        'departments': Department.objects.order_by('name'),
    }
    return render(request, 'resources/resource_list.html', context)


@login_required
def service_list(request):
    """Show team-owned services."""
    return _resource_list(request, TeamResource.ResourceType.SERVICE)


@login_required
def repository_list(request):
    """Show team-owned repositories."""
    return _resource_list(request, TeamResource.ResourceType.REPOSITORY)


@login_required
def contact_channel_list(request):
    """Show team-owned contact channels."""
    return _resource_list(request, TeamResource.ResourceType.CONTACT_CHANNEL)


@login_required
@user_passes_test(superuser_required)
def resource_create(request, resource_type):
    """Create a new resource for the selected type."""
    config = _get_resource_config(resource_type)
    if config is None:
        messages.error(request, 'Unknown resource type.')
        return redirect('core:home')

    if request.method == 'POST':
        form = TeamResourceForm(request.POST, resource_type=resource_type)
        if form.is_valid():
            form.save()
            messages.success(request, f'{config["singular"]} created successfully.')
            return redirect(config['list_url_name'])
    else:
        form = TeamResourceForm(resource_type=resource_type)

    context = {
        'form': form,
        'config': config,
        'resource_type': resource_type,
        'form_mode': 'Create',
    }
    return render(request, 'resources/resource_form.html', context)


@login_required
@user_passes_test(superuser_required)
def resource_update(request, pk):
    """Update an existing team resource."""
    resource = get_object_or_404(TeamResource.objects.select_related('team'), pk=pk)
    config = RESOURCE_PAGE_CONFIG[resource.resource_type]

    if request.method == 'POST':
        form = TeamResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f'{config["singular"]} updated successfully.')
            return redirect(config['list_url_name'])
    else:
        form = TeamResourceForm(instance=resource)

    context = {
        'form': form,
        'resource': resource,
        'config': config,
        'resource_type': resource.resource_type,
        'form_mode': 'Edit',
    }
    return render(request, 'resources/resource_form.html', context)


@require_POST
@login_required
@user_passes_test(superuser_required)
def resource_deactivate(request, pk):
    """Soft-deactivate a resource instead of deleting it permanently."""
    resource = get_object_or_404(TeamResource, pk=pk)
    resource.is_active = False
    resource.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, 'Resource deactivated successfully.')
    return redirect(RESOURCE_PAGE_CONFIG[resource.resource_type]['list_url_name'])


@require_POST
@login_required
@user_passes_test(superuser_required)
def resource_reactivate(request, pk):
    """Reactivate a previously inactive resource."""
    resource = get_object_or_404(TeamResource, pk=pk)
    resource.is_active = True
    resource.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, 'Resource reactivated successfully.')
    return redirect(RESOURCE_PAGE_CONFIG[resource.resource_type]['list_url_name'])
