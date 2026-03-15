from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CharacterForm, WorldForm
from .models import Character, Post, World


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
def world_timeline(request, world_id):
	world = get_object_or_404(World, id=world_id)
	posts = Post.objects.filter(world=world).select_related('character', 'author')
	return render(request, 'worlds/world_timeline.html', {'world': world, 'posts': posts})


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


@login_required
def character_list(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)
	characters = Character.objects.filter(world=world)
	return render(request, 'worlds/character_list.html', {'world': world, 'characters': characters})


@login_required
def character_create(request, world_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)

	if request.method == 'POST':
		form = CharacterForm(request.POST)
		if form.is_valid():
			character = form.save(commit=False)
			character.world = world
			character.save()
			return redirect('character_list', world_id=world.id)
	else:
		form = CharacterForm()

	return render(request, 'worlds/character_form.html', {'form': form, 'mode': 'create', 'world': world})


@login_required
def character_edit(request, world_id, character_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)
	character = get_object_or_404(Character, id=character_id, world=world)

	if request.method == 'POST':
		form = CharacterForm(request.POST, instance=character)
		if form.is_valid():
			form.save()
			return redirect('character_list', world_id=world.id)
	else:
		form = CharacterForm(instance=character)

	return render(
		request,
		'worlds/character_form.html',
		{'form': form, 'mode': 'edit', 'world': world, 'character': character},
	)


@login_required
def character_delete(request, world_id, character_id):
	world = get_object_or_404(World, id=world_id, owner=request.user)
	character = get_object_or_404(Character, id=character_id, world=world)

	if request.method == 'POST':
		character.delete()
		return redirect('character_list', world_id=world.id)

	return render(request, 'worlds/character_confirm_delete.html', {'world': world, 'character': character})
