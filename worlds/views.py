from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WorldForm
from .models import World


@login_required
def world_list(request):
	worlds = World.objects.filter(owner=request.user)
	return render(request, 'worlds/world_list.html', {'worlds': worlds})


@login_required
def world_create(request):
	if request.method == 'POST':
		form = WorldForm(request.POST)
		if form.is_valid():
			world = form.save(commit=False)
			world.owner = request.user
			world.save()
			return redirect('world_list')
	else:
		form = WorldForm()

	return render(request, 'worlds/world_form.html', {'form': form, 'mode': 'create'})


@login_required
def world_edit(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		form = WorldForm(request.POST, instance=world)
		if form.is_valid():
			form.save()
			return redirect('world_list')
	else:
		form = WorldForm(instance=world)

	return render(request, 'worlds/world_form.html', {'form': form, 'mode': 'edit', 'world': world})


@login_required
def world_delete(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		world.delete()
		return redirect('world_list')

	return render(request, 'worlds/world_confirm_delete.html', {'world': world})
