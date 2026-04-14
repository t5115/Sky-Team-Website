from django.shortcuts import get_object_or_404, redirect, render
from .models import Profile

# Create your views here.
def profile_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)  
    return render(request, 'profile.html', {'profile': profile})
def profile_edit(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    if request.method == "POST":
        profile.name = request.POST.get("name")
        profile.department = request.POST.get("department")
        profile.role = request.POST.get("role")
        profile.team = request.POST.get("team")
        profile.email = request.POST.get("email")
        profile.phone_number = request.POST.get("phone_number")
        profile.save()

        return redirect("profile_view", profile_id=profile.id)

    return render(request, "profile_edit.html", {"profile": profile})