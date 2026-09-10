extends Node2D
class_name EncounterSite

signal encounter_activated(site: EncounterSite)
signal encounter_deactivated(site: EncounterSite)
signal encounter_cleared(site: EncounterSite)

const ENEMY_SCENE: PackedScene = preload("res://entities/enemy/enemy.tscn")
const DELAYED_SPAWN_SECONDS: float = 0.45

var site_id: StringName = &""
var site_kind: StringName = &"encounter"
var display_name: String = "Encounter"
var discovery_radius: float = 285.0
var activation_radius: float = 145.0
var retreat_radius: float = 330.0

var _state: ExpeditionState = null
var _hero: Hero = null
var _label: Label = null
var _active: bool = false
var _activation_generation: int = 0
var _pending_delayed_spawn: bool = false
var _live_enemies: Array[Enemy] = []

func configure(descriptor: Dictionary, state: ExpeditionState, hero: Hero) -> void:
	site_id = StringName(descriptor[&"id"])
	site_kind = StringName(descriptor[&"kind"])
	display_name = String(descriptor[&"display_name"])
	position = descriptor[&"position"]
	discovery_radius = float(descriptor[&"discovery_radius"])
	activation_radius = float(descriptor[&"activation_radius"])
	retreat_radius = float(descriptor[&"retreat_radius"])
	_state = state
	_hero = hero
	_state.register_place(site_id)

func _ready() -> void:
	_label = Label.new()
	_label.position = Vector2(-105.0, -74.0)
	_label.size = Vector2(210.0, 54.0)
	_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_label.add_theme_font_size_override(&"font_size", 15)
	add_child(_label)
	refresh_visual()

func _physics_process(_delta: float) -> void:
	if not is_instance_valid(_hero) or _hero.is_dead() or _state.is_cleared(site_id):
		return
	var distance_to_hero := global_position.distance_to(_hero.global_position)
	if distance_to_hero <= discovery_radius and _state.mark_discovered(site_id):
		refresh_visual()
	if not _active and distance_to_hero <= activation_radius:
		_activate()
	elif _active and distance_to_hero >= retreat_radius:
		deactivate()

func is_active() -> bool:
	return _active

func is_cleared() -> bool:
	return _state != null and _state.is_cleared(site_id)

func active_enemies() -> Array[Enemy]:
	var result: Array[Enemy] = []
	for enemy: Enemy in _live_enemies:
		if is_instance_valid(enemy) and not enemy.is_dead():
			result.append(enemy)
	return result

func allows_target(enemy: Enemy) -> bool:
	if not _active or not is_instance_valid(_hero) or not is_instance_valid(enemy) or enemy.is_dead():
		return false
	if not _live_enemies.has(enemy):
		return false
	return (
		_hero.global_position.distance_to(global_position) < retreat_radius
		and enemy.global_position.distance_to(global_position) < retreat_radius
	)

func deactivate() -> void:
	if not _active:
		return
	_active = false
	_activation_generation += 1
	_pending_delayed_spawn = false
	for enemy: Enemy in _live_enemies:
		if is_instance_valid(enemy):
			enemy.queue_free()
	_live_enemies.clear()
	_state.mark_dormant(site_id)
	refresh_visual()
	encounter_deactivated.emit(self)

func refresh_visual() -> void:
	queue_redraw()
	if not is_instance_valid(_label) or _state == null:
		return
	if _state.is_cleared(site_id):
		if site_kind == &"ruins" and not _state.is_reward_claimed(site_id):
			_label.text = "%s\nREWARD READY" % display_name
		else:
			_label.text = "%s\nCLEARED" % display_name
	elif _active:
		_label.text = "%s\nACTIVE DANGER" % display_name
	elif _state.is_discovered(site_id):
		_label.text = "%s\nDANGER • approach to engage" % display_name
	else:
		_label.text = "DANGER SIGN\nunknown place"

func snapshot() -> Dictionary[StringName, Variant]:
	return {
		&"id": site_id,
		&"kind": site_kind,
		&"position": global_position,
		&"state": _state.site_state(site_id) if _state != null else &"missing",
		&"discovered": _state.is_discovered(site_id) if _state != null else false,
		&"active": _active,
		&"cleared": is_cleared(),
		&"activation_generation": _activation_generation,
		&"live_enemy_count": active_enemies().size(),
		&"pending_spawn": _pending_delayed_spawn,
	}

func _activate() -> void:
	if _active or _state.is_cleared(site_id):
		return
	_active = true
	_activation_generation += 1
	_state.mark_active(site_id)
	_spawn_enemy(Vector2(-34.0, 10.0))
	_pending_delayed_spawn = true
	var expected_generation := _activation_generation
	get_tree().create_timer(DELAYED_SPAWN_SECONDS).timeout.connect(
		_on_delayed_spawn.bind(expected_generation)
	)
	refresh_visual()
	encounter_activated.emit(self)

func _on_delayed_spawn(expected_generation: int) -> void:
	if expected_generation != _activation_generation or not _active or _state.is_cleared(site_id):
		return
	_pending_delayed_spawn = false
	_spawn_enemy(Vector2(42.0, -20.0))
	_check_for_clear()

func _spawn_enemy(local_offset: Vector2) -> void:
	var enemy := ENEMY_SCENE.instantiate() as Enemy
	assert(enemy != null)
	enemy.position = local_offset
	add_child(enemy)
	enemy.configure_combat(_hero, global_position, retreat_radius - 25.0)
	enemy.died.connect(_on_enemy_died)
	_live_enemies.append(enemy)

func _on_enemy_died(enemy: Enemy) -> void:
	_live_enemies.erase(enemy)
	if is_instance_valid(enemy):
		enemy.queue_free()
	_check_for_clear()

func _check_for_clear() -> void:
	if _active and _live_enemies.is_empty() and not _pending_delayed_spawn:
		_active = false
		_activation_generation += 1
		_state.mark_cleared(site_id)
		refresh_visual()
		encounter_cleared.emit(self)

func _draw() -> void:
	var state_color := Color("d8a657")
	if _state != null and _state.is_cleared(site_id):
		state_color = Color("63d6b2")
	elif _active:
		state_color = Color("f05b65")
	elif _state != null and not _state.is_discovered(site_id):
		state_color = Color("746a86")

	draw_circle(Vector2.ZERO, activation_radius, Color(state_color, 0.09))
	draw_arc(Vector2.ZERO, activation_radius, 0.0, TAU, 64, Color(state_color, 0.80), 3.0)
	if site_kind == &"ruins":
		draw_rect(Rect2(-34.0, -28.0, 68.0, 56.0), Color(state_color, 0.34), true)
		draw_rect(Rect2(-34.0, -28.0, 68.0, 56.0), state_color, false, 4.0)
		draw_line(Vector2(-34.0, -28.0), Vector2(0.0, -52.0), state_color, 4.0)
		draw_line(Vector2(0.0, -52.0), Vector2(34.0, -28.0), state_color, 4.0)
	else:
		draw_circle(Vector2.ZERO, 28.0, Color(state_color, 0.34))
		draw_arc(Vector2.ZERO, 28.0, 0.0, TAU, 32, state_color, 4.0)
