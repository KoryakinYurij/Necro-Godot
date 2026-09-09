extends GutTest

const EXPEDITION_SCENE: PackedScene = preload("res://expedition/expedition.tscn")


func _spawn_expedition() -> Expedition:
	var expedition: Expedition = EXPEDITION_SCENE.instantiate() as Expedition
	assert_not_null(expedition)
	add_child_autofree(expedition)
	return expedition


func test_enemy_deals_damage_through_running_combat_loop() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(50)
	var snapshot: Dictionary[StringName, Variant] = expedition.combat_snapshot()
	assert_lt(int(snapshot[&"hero_health"]), int(snapshot[&"hero_max_health"]))


func test_autonomous_minion_acquires_and_defeats_live_enemy() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(110)
	var snapshot: Dictionary[StringName, Variant] = expedition.combat_snapshot()
	assert_false(bool(snapshot[&"enemy_alive"]))
	assert_false(bool(snapshot[&"minion_has_target"]))


func test_lethal_damage_then_restart_creates_fresh_combat_state() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(2)
	var before: Dictionary[StringName, Variant] = expedition.combat_snapshot()
	expedition.apply_hero_damage(999)
	await wait_physics_frames(1)
	var dead_state: Dictionary[StringName, Variant] = expedition.combat_snapshot()
	assert_true(bool(dead_state[&"dead"]))
	assert_eq(int(dead_state[&"hero_health"]), 0)

	var restart_event := InputEventAction.new()
	restart_event.action = &"restart"
	restart_event.pressed = true
	Input.parse_input_event(restart_event)
	await wait_physics_frames(2)
	var restarted: Dictionary[StringName, Variant] = expedition.combat_snapshot()
	assert_eq(int(restarted[&"generation"]), int(before[&"generation"]) + 1)
	assert_false(bool(restarted[&"dead"]))
	assert_eq(int(restarted[&"hero_health"]), int(restarted[&"hero_max_health"]))
	assert_true(bool(restarted[&"enemy_alive"]))
	assert_eq(int(restarted[&"enemy_health"]), int(restarted[&"enemy_max_health"]))
