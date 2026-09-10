extends CharacterBody2D
class_name Hero

signal health_changed(current: int, maximum: int)
signal died

@export var move_speed: float = 220.0
@export var movement_bounds: Rect2 = Rect2(-1100.0, -700.0, 2200.0, 1400.0)

@onready var health: HealthComponent = %Health
@onready var follow_camera: Camera2D = %FollowCamera


func _ready() -> void:
	health.health_changed.connect(_on_health_changed)
	health.died.connect(_on_died)
	queue_redraw()


func _physics_process(_delta: float) -> void:
	if health.dead:
		velocity = Vector2.ZERO
		return
	var direction: Vector2 = Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	velocity = direction * move_speed
	move_and_slide()
	global_position = Vector2(
		clampf(global_position.x, movement_bounds.position.x, movement_bounds.end.x),
		clampf(global_position.y, movement_bounds.position.y, movement_bounds.end.y)
	)


func activate_camera() -> void:
	follow_camera.make_current()
	follow_camera.reset_smoothing()


func receive_damage(amount: int) -> void:
	health.take_damage(amount)


func get_health() -> int:
	return health.current_health


func get_max_health() -> int:
	return health.max_health


func is_dead() -> bool:
	return health.dead


func _on_health_changed(current: int, maximum: int) -> void:
	health_changed.emit(current, maximum)


func _on_died() -> void:
	velocity = Vector2.ZERO
	queue_redraw()
	died.emit()


func _draw() -> void:
	var body_color: Color = Color("7652d9") if not health.dead else Color("4d465e")
	draw_circle(Vector2.ZERO, 18.0, body_color)
	draw_circle(Vector2(0.0, -5.0), 9.0, Color("d8ccff"))
	draw_line(Vector2(-14.0, 16.0), Vector2(14.0, 16.0), Color("2b203f"), 4.0)


func increase_max_health(amount: int) -> void:
	health.increase_max_health(amount, amount)


func add_move_speed(amount: float) -> void:
	if amount > 0.0:
		move_speed += amount
