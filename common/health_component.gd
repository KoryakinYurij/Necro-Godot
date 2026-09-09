extends Node
class_name HealthComponent

signal health_changed(current: int, maximum: int)
signal died

@export var max_health: int = 100

var current_health: int = 0
var dead: bool = false


func _ready() -> void:
	reset()


func reset() -> void:
	current_health = max_health
	dead = false
	health_changed.emit(current_health, max_health)


func take_damage(amount: int) -> void:
	if amount <= 0 or dead:
		return
	current_health = maxi(current_health - amount, 0)
	health_changed.emit(current_health, max_health)
	if current_health == 0:
		dead = true
		died.emit()
