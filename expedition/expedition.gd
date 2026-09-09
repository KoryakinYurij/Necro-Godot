extends Node2D
class_name Expedition

signal run_restarted(generation: int)
signal player_died

const HERO_SCENE: PackedScene = preload("res://entities/hero/hero.tscn")
const MINION_SCENE: PackedScene = preload("res://entities/minion/minion.tscn")
const ENEMY_SCENE: PackedScene = preload("res://entities/enemy/enemy.tscn")

@onready var status_label: Label = %StatusLabel
@onready var death_label: Label = %DeathLabel
@onready var help_label: Label = %HelpLabel

var hero: Hero = null
var minion: AutonomousMinion = null
var enemy: Enemy = null
var _run_root: Node2D = null
var _generation: int = 0
var _player_dead: bool = false


func _ready() -> void:
	_build_run()
	queue_redraw()


func _process(_delta: float) -> void:
	_update_hud()


func _unhandled_input(event: InputEvent) -> void:
	if _player_dead and event.is_action_pressed(&"restart"):
		restart_expedition()


func restart_expedition() -> void:
	_build_run()


func combat_snapshot() -> Dictionary[StringName, Variant]:
	var snapshot: Dictionary[StringName, Variant] = {
		&"generation": _generation,
		&"dead": _player_dead,
		&"hero_health": hero.get_health() if is_instance_valid(hero) else -1,
		&"hero_max_health": hero.get_max_health() if is_instance_valid(hero) else -1,
		&"enemy_alive": is_instance_valid(enemy) and not enemy.is_dead(),
		&"enemy_health": enemy.get_health() if is_instance_valid(enemy) else 0,
		&"enemy_max_health": enemy.get_max_health() if is_instance_valid(enemy) else 0,
		&"minion_has_target": is_instance_valid(minion) and minion.has_live_target(),
	}
	return snapshot


func _build_run() -> void:
	_generation += 1
	_player_dead = false
	if is_instance_valid(_run_root):
		_run_root.free()
	_run_root = Node2D.new()
	_run_root.name = "Run"
	add_child(_run_root)

	hero = HERO_SCENE.instantiate() as Hero
	minion = MINION_SCENE.instantiate() as AutonomousMinion
	enemy = ENEMY_SCENE.instantiate() as Enemy
	assert(hero != null and minion != null and enemy != null)
	hero.position = Vector2.ZERO
	minion.position = Vector2(-34.0, 28.0)
	enemy.position = Vector2(55.0, 0.0)
	_run_root.add_child(hero)
	_run_root.add_child(minion)
	_run_root.add_child(enemy)
	minion.set_owner_hero(hero)
	enemy.set_target(hero)
	hero.call_deferred(&"activate_camera")
	hero.died.connect(_on_hero_died)
	run_restarted.emit(_generation)
	_update_hud()


func _on_hero_died() -> void:
	_player_dead = true
	player_died.emit()
	_update_hud()


func _update_hud() -> void:
	if not is_instance_valid(status_label) or not is_instance_valid(hero):
		return
	var enemy_text: String = "defeated" if not is_instance_valid(enemy) or enemy.is_dead() else "%d/%d" % [enemy.get_health(), enemy.get_max_health()]
	status_label.text = "Expedition %d   Hero HP %d/%d   Enemy %s" % [_generation, hero.get_health(), hero.get_max_health(), enemy_text]
	death_label.visible = _player_dead
	death_label.text = "YOU DIED\nPress R to begin a clean Expedition"
	help_label.text = "WASD / arrows move   •   Minion fights autonomously   •   R restarts after death"


func _draw() -> void:
	draw_rect(Rect2(-1200.0, -800.0, 2400.0, 1600.0), Color("151025"), true)
	for x: int in range(-1200, 1201, 80):
		draw_line(Vector2(x, -800.0), Vector2(x, 800.0), Color(0.20, 0.16, 0.30, 0.45), 1.0)
	for y: int in range(-800, 801, 80):
		draw_line(Vector2(-1200.0, y), Vector2(1200.0, y), Color(0.20, 0.16, 0.30, 0.45), 1.0)
	draw_rect(Rect2(-1200.0, -800.0, 2400.0, 1600.0), Color("6f5d92"), false, 3.0)
