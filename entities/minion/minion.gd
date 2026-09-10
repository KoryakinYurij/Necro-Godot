extends CharacterBody2D
class_name AutonomousMinion

@export var move_speed: float = 230.0
@export var follow_distance: float = 54.0
@export var attack_range: float = 85.0
@export var attack_damage: int = 10
@export var attack_cooldown: float = 0.30
@export var reacquire_interval: float = 0.15

var owner_hero: Hero = null
var target: Enemy = null
var combat_site: EncounterSite = null
var _attack_remaining: float = 0.0
var _reacquire_remaining: float = 0.0

func _ready() -> void:
	queue_redraw()

func _physics_process(delta: float) -> void:
	_attack_remaining = maxf(_attack_remaining - delta, 0.0)
	_reacquire_remaining = maxf(_reacquire_remaining - delta, 0.0)
	if not is_instance_valid(owner_hero) or owner_hero.is_dead():
		velocity = Vector2.ZERO
		target = null
		return
	if has_live_target() and (not is_instance_valid(combat_site) or not combat_site.allows_target(target)):
		target = null
	if not has_live_target() and _reacquire_remaining <= 0.0:
		_acquire_nearest_enemy()
		_reacquire_remaining = reacquire_interval
	if has_live_target():
		_fight_target()
	else:
		_follow_owner()

func set_owner_hero(hero: Hero) -> void:
	owner_hero = hero

func set_combat_site(site: EncounterSite) -> void:
	combat_site = site
	target = null
	_reacquire_remaining = 0.0

func clear_combat_site(site: EncounterSite) -> void:
	if combat_site == site:
		combat_site = null
		target = null

func has_live_target() -> bool:
	return is_instance_valid(target) and not target.is_dead()

func _acquire_nearest_enemy() -> void:
	target = null
	if not is_instance_valid(combat_site) or not combat_site.is_active():
		return
	var nearest_distance: float = INF
	for candidate: Enemy in combat_site.active_enemies():
		if not combat_site.allows_target(candidate):
			continue
		var distance := global_position.distance_squared_to(candidate.global_position)
		if distance < nearest_distance:
			nearest_distance = distance
			target = candidate

func _fight_target() -> void:
	if not has_live_target():
		target = null
		return
	var offset := target.global_position - global_position
	if offset.length() > attack_range:
		velocity = offset.normalized() * move_speed
		move_and_slide()
		return
	velocity = Vector2.ZERO
	if _attack_remaining <= 0.0:
		target.receive_damage(attack_damage)
		_attack_remaining = attack_cooldown
		# Damage can synchronously clear the Encounter and therefore clear target.
		if not is_instance_valid(target) or target.is_dead():
			target = null

func _follow_owner() -> void:
	var offset := owner_hero.global_position - global_position
	if offset.length() > follow_distance:
		velocity = offset.normalized() * move_speed
		move_and_slide()
	else:
		velocity = Vector2.ZERO

func _draw() -> void:
	draw_circle(Vector2.ZERO, 12.0, Color("63d6b2"))
	draw_circle(Vector2.ZERO, 5.0, Color("e1fff5"))
