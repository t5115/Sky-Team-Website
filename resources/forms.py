from django import forms

from .models import TeamResource


class TeamResourceForm(forms.ModelForm):
    """
    Form used by admins to create and update team resources.

    The resource_type is injected by the view when creating a resource from one
    of the sidebar pages. This keeps the user on the correct flow: Services page
    creates services, Repositories page creates repositories, etc.
    """

    class Meta:
        model = TeamResource
        fields = ['team', 'name', 'url', 'contact_detail', 'description', 'is_active']
        widgets = {
            'team': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Backend API Repository',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...',
            }),
            'contact_detail': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: #backend-support or team email address',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explain what this resource is used for.',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'team': 'Owning team',
            'name': 'Resource name',
            'url': 'URL',
            'contact_detail': 'Contact detail',
            'description': 'Description',
            'is_active': 'Active',
        }

    def __init__(self, *args, resource_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource_type = resource_type

        # Help text changes depending on the page the user came from.
        if resource_type == TeamResource.ResourceType.REPOSITORY:
            self.fields['url'].required = True
            self.fields['url'].help_text = 'Required for repository resources.'
        elif resource_type == TeamResource.ResourceType.CONTACT_CHANNEL:
            self.fields['url'].required = False
            self.fields['contact_detail'].help_text = 'Required if no URL is provided.'
        else:
            self.fields['url'].required = False

    def save(self, commit=True):
        resource = super().save(commit=False)

        # On create, the view passes the type. On update, keep the existing type.
        if self.resource_type:
            resource.resource_type = self.resource_type

        if commit:
            resource.save()

        return resource
