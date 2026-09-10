extends Node2D
class_name Expedition

signal run_restarted(generation: int)
signal player_died

const HERO_SCENE: PackedScene = preload("res://entities/hero/hero.tscn")
const MINION_SCENE: PackedScene = preload("res://entities/minion/minion.tscn")
const ENCOUNTER_SITE_SCRIPT: Script = preload("res://encounters/encounter_site.gd")

@export var expedition_seed: int = WorldDescription.DEFAULT_SEED

@onready var status_label: Label = %StatusLabel
@onready var objective_label: Label = %ObjectiveLabel
@onready var death_label: Label = %DeathLabel
@onready var help_label: Label = %HelpLabel
@onready var reward_effect_label: Label = %RewardEffectLabel
@onready var reward_overlay: Control = %RewardOverlay
@onready var reward_title_label: Label = %RewardTitleLabel
@onready var vigor_button: Button = %VigorButton
@onready var haste_button: Button = %HasteButton

var hero: Hero = null
var minion: AutonomousMinion = null
var _run_root: Node2D = null
var _world_root: Node2D = null
var _world_description: WorldDescription = null
var _expedition_state: ExpeditionState = null
var _sites: Dictionary[StringName, EncounterSite] = {}
var _generation: int = 0
var _player_dead: bool = false
var _active_site_id: StringName = &""
var _modal_owner: StringName = &""
var _reward_site_id: StringName = &""
var _reward_effect_text: String = "No blessing yet"

func _ready() -> void:
	vigor_button.pressed.connect(_on_reward_button.bind(&"vigor"))
	haste_button.pressed.connect(_on_reward_button.bind(&"haste"))
	_build_run()
	queue_redraw()

func _process(_delta: float) -> void:
	_update_hud()

func _unhandled_input(event: InputEvent) -> void:
	if _player_dead and event.is_action_pressed(&"restart"):
		restart_expedition()

func restart_expedition() -> void:
	_build_run()

func get_site(site_id: StringName) -> EncounterSite:
	return _sites.get(site_id, null)

func world_place(site_id: StringName) -> Dictionary:
	return _world_description.place(site_id) if _world_description != null else {}

func choose_reward(reward_id: StringName) -> bool:
	if _modal_owner != &"ruins_reward" or _reward_site_id == &"" or _expedition_state == null:
		return false
	if reward_id != &"vigor" and reward_id != &"haste":
		return false
	var site_id := _reward_site_id
	if not _expedition_state.claim_reward(site_id, reward_id):
		return false
	match reward_id:
		&"vigor":
			hero.increase_max_health(30)
			_reward_effect_text = "Bone Ward: +30 max HP (and healed 30)"
		&"haste":
			hero.add_move_speed(55.0)
			_reward_effect_text = "Grave Haste: +55 movement speed"
	var reward_site := get_site(site_id)
	if is_instance_valid(reward_site):
		reward_site.refresh_visual()
	_modal_owner = &""
	_reward_site_id = &""
	reward_overlay.visible = false
	get_tree().paused = false
	_update_hud()
	return true

func exploration_snapshot() -> Dictionary[StringName, Variant]:
	var site_snapshots: Dictionary[StringName, Variant] = {}
	for site_id: StringName in _sites:
		site_snapshots[site_id] = _sites[site_id].snapshot()
	return {
		&"generation": _generation,
		&"seed": expedition_seed,
		&"dead": _player_dead,
		&"hero_position": hero.global_position if is_instance_valid(hero) else Vector2.ZERO,
		&"hero_health": hero.get_health() if is_instance_valid(hero) else -1,
		&"hero_max_health": hero.get_max_health() if is_instance_valid(hero) else -1,
		&"hero_move_speed": hero.move_speed if is_instance_valid(hero) else 0.0,
		&"active_site": _active_site_id,
		&"modal_owner": _modal_owner,
		&"tree_paused": get_tree().paused,
		&"reward_effect": _reward_effect_text,
		&"ruins_reward": _expedition_state.reward_for(&"ruins") if _expedition_state != null else &"",
		&"sites": site_snapshots,
	}

func combat_snapshot() -> Dictionary[StringName, Variant]:
	var enemy_alive := false
	var enemy_health := 0
	var enemy_max_health := 0
	for site_id: StringName in _sites:
		var enemies := _sites[site_id].active_enemies()
		if not enemies.is_empty():
			enemy_alive = true
			enemy_health = enemies[0].get_health()
			enemy_max_health = enemies[0].get_max_health()
			break
	return {
		&"generation": _generation,
		&"dead": _player_dead,
		&"hero_health": hero.get_health() if is_instance_valid(hero) else -1,
		&"hero_max_health": hero.get_max_health() if is_instance_valid(hero) else -1,
		&"enemy_alive": enemy_alive,
		&"enemy_health": enemy_health,
		&"enemy_max_health": enemy_max_health,
		&"minion_has_target": is_instance_valid(minion) and minion.has_live_target(),
	}

func _build_run() -> void:
	if get_tree().paused:
		get_tree().paused = false
	_modal_owner = &""
	_reward_site_id = &""
	_reward_effect_text = "No blessing yet"
	reward_overlay.visible = false
	_generation += 1
	_player_dead = false
	_active_site_id = &""
	if is_instance_valid(_run_root):
		_run_root.free()
	_run_root = Node2D.new()
	_run_root.name = "Run"
	add_child(_run_root)

	_world_description = WorldDescription.new(expedition_seed)
	_expedition_state = ExpeditionState.new()
	_world_root = Node2D.new()
	_world_root.name = "World"
	_run_root.add_child(_world_root)

	hero = HERO_SCENE.instantiate() as Hero
	minion = MINION_SCENE.instantiate() as AutonomousMinion
	assert(hero != null and minion != null)
	hero.position = Vector2.ZERO
	minion.position = Vector2(-34.0, 28.0)
	_run_root.add_child(hero)
	_run_root.add_child(minion)
	minion.set_owner_hero(hero)

	_sites.clear()
	for descriptor: Dictionary in _world_description.places():
		var site := ENCOUNTER_SITE_SCRIPT.new() as EncounterSite
		assert(site != null)
		site.name = String(descriptor[&"id"]).to_pascal_case()
		site.configure(descriptor, _expedition_state, hero)
		_world_root.add_child(site)
		site.encounter_activated.connect(_on_encounter_activated)
		site.encounter_deactivated.connect(_on_encounter_deactivated)
		site.encounter_cleared.connect(_on_encounter_cleared)
		_sites[site.site_id] = site

	hero.call_deferred(&"activate_camera")
	hero.died.connect(_on_hero_died)
	run_restarted.emit(_generation)
	_update_hud()

func _on_encounter_activated(site: EncounterSite) -> void:
	_active_site_id = site.site_id
	minion.set_combat_site(site)
	_update_hud()

func _on_encounter_deactivated(site: EncounterSite) -> void:
	if _active_site_id == site.site_id:
		_active_site_id = &""
	minion.clear_combat_site(site)
	_update_hud()

func _on_encounter_cleared(site: EncounterSite) -> void:
	if _active_site_id == site.site_id:
		_active_site_id = &""
	minion.clear_combat_site(site)
	if site.site_kind == &"ruins" and not _player_dead:
		call_deferred(&"_offer_ruins_reward", site.site_id)
	_update_hud()

func _offer_ruins_reward(site_id: StringName) -> void:
	if _player_dead or _expedition_state.is_reward_claimed(site_id) or _modal_owner != &"":
		return
	_modal_owner = &"ruins_reward"
	_reward_site_id = site_id
	reward_title_label.text = "RUINS CLEARED\nChoose one Expedition blessing"
	reward_overlay.visible = true
	get_tree().paused = true
	vigor_button.grab_focus()
	_update_hud()

func _on_reward_button(reward_id: StringName) -> void:
	choose_reward(reward_id)

func _on_hero_died() -> void:
	_player_dead = true
	player_died.emit()
	_update_hud()

func _update_hud() -> void:
	if not is_instance_valid(status_label) or not is_instance_valid(hero):
		return
	status_label.text = "Expedition %d   Seed %d   HP %d/%d" % [
		_generation, expedition_seed, hero.get_health(), hero.get_max_health()
	]
	if _modal_owner == &"ruins_reward":
		objective_label.text = "RUINS CLEARED • choose a blessing"
	elif _active_site_id != &"":
		objective_label.text = "Encounter active • fight or retreat beyond the danger ring"
	elif _expedition_state.is_reward_claimed(&"ruins"):
		objective_label.text = "Reward claimed • keep exploring; cleared places stay cleared"
	else:
		objective_label.text = "Explore freely • approach a danger ring to engage"
	reward_effect_label.text = "Blessing: %s" % _reward_effect_text
	death_label.visible = _player_dead
	death_label.text = "YOU DIED\nPress R to begin a clean Expedition"
	help_label.text = (
		"WASD / arrows move   •   amber danger   •   red active   •   "
		+ "teal cleared   •   minion fights locally"
	)

func _draw() -> void:
	draw_rect(Rect2(-1200.0, -800.0, 2400.0, 1600.0), Color("151025"), true)
	for x: int in range(-1200, 1201, 80):
		draw_line(
			Vector2(x, -800.0), Vector2(x, 800.0),
			Color(0.20, 0.16, 0.30, 0.45), 1.0
		)
	for y: int in range(-800, 801, 80):
		draw_line(
			Vector2(-1200.0, y), Vector2(1200.0, y),
			Color(0.20, 0.16, 0.30, 0.45), 1.0
		)
	draw_circle(Vector2.ZERO, 48.0, Color(0.36, 0.28, 0.52, 0.22))
	draw_string(
		ThemeDB.fallback_font, Vector2(-52.0, 82.0), "START",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("9587ad")
	)
	draw_rect(
		Rect2(-1200.0, -800.0, 2400.0, 1600.0),
		Color("6f5d92"), false, 3.0
	)
