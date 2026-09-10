extends CharacterBody2D
class_name Enemy

signal health_changed(current: int, maximum: int)
signal died(enemy: Enemy)

@export var move_speed: float = 95.0
@export var attack_damage: int = 6
@export var attack_range: float = 38.0
@export var attack_cooldown: float = 0.65

@onready var health: HealthComponent = %Health

var target: Hero = null
var _attack_remaining: float = 0.0
var _leash_center: Vector2 = Vector2.ZERO
var _leash_radius: float = 0.0
var _has_leash: bool = false

func _ready() -> void:
	health.health_changed.connect(_on_health_changed)
	health.died.connect(_on_died)
	queue_redraw()

func _physics_process(delta: float) -> void:
	_attack_remaining = maxf(_attack_remaining - delta, 0.0)
	if health.dead or not is_instance_valid(target) or target.is_dead():
		velocity = Vector2.ZERO
		return
	if _has_leash and target.global_position.distance_to(_leash_center) > _leash_radius:
		_return_to_leash()
		return
	var offset := target.global_position - global_position
	if offset.length() > attack_range:
		velocity = offset.normalized() * move_speed
		move_and_slide()
	else:
		velocity = Vector2.ZERO
		if _attack_remaining <= 0.0:
			target.receive_damage(attack_damage)
			_attack_remaining = attack_cooldown

func configure_combat(hero: Hero, leash_center: Vector2, leash_radius: float) -> void:
	target = hero
	_leash_center = leash_center
	_leash_radius = leash_radius
	_has_leash = true

func set_target(hero: Hero) -> void:
	target = hero

func receive_damage(amount: int) -> void:
	health.take_damage(amount)

func get_health() -> int:
	return health.current_health

func get_max_health() -> int:
	return health.max_health

func is_dead() -> bool:
	return health.dead

func _return_to_leash() -> void:
	var home_offset := _leash_center - global_position
	if home_offset.length() > 18.0:
		velocity = home_offset.normalized() * move_speed
		move_and_slide()
	else:
		velocity = Vector2.ZERO

func _on_health_changed(current: int, maximum: int) -> void:
	health_changed.emit(current, maximum)

func _on_died() -> void:
	velocity = Vector2.ZERO
	collision_layer = 0
	collision_mask = 0
	visible = false
	set_physics_process(false)
	died.emit(self)

func _draw() -> void:
	draw_circle(Vector2.ZERO, 17.0, Color("d94b62"))
	draw_circle(Vector2(-6.0, -4.0), 3.0, Color("ffe7e7"))
	draw_circle(Vector2(6.0, -4.0), 3.0, Color("ffe7e7"))
