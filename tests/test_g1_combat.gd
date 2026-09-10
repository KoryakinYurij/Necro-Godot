extends GutTest

const EXPEDITION_SCENE: PackedScene = preload("res://expedition/expedition.tscn")

func _spawn_expedition() -> Expedition:
	var expedition := EXPEDITION_SCENE.instantiate() as Expedition
	assert_not_null(expedition)
	add_child_autofree(expedition)
	return expedition

func _press_restart() -> void:
	var pressed := InputEventAction.new()
	pressed.action = &"restart"
	pressed.pressed = true
	Input.parse_input_event(pressed)
	var released := InputEventAction.new()
	released.action = &"restart"
	released.pressed = false
	Input.parse_input_event(released)

func test_fresh_expedition_is_safe_until_local_encounter_is_chosen() -> void:
	var expedition := _spawn_expedition()
	await wait_physics_frames(10)
	var snapshot := expedition.combat_snapshot()
	assert_false(bool(snapshot[&"dead"]))
	assert_false(bool(snapshot[&"enemy_alive"]))
	assert_false(bool(snapshot[&"minion_has_target"]))

func test_restart_event_creates_fresh_hero_and_camera() -> void:
	var expedition := _spawn_expedition()
	await wait_physics_frames(3)
	expedition.hero.receive_damage(999)
	assert_true(bool(expedition.combat_snapshot()[&"dead"]))
	_press_restart()
	await wait_physics_frames(3)
	var restarted := expedition.exploration_snapshot()
	assert_eq(int(restarted[&"generation"]), 2)
	assert_false(bool(restarted[&"dead"]))
	assert_eq(int(restarted[&"hero_health"]), int(restarted[&"hero_max_health"]))
	var active_camera := expedition.get_viewport().get_camera_2d()
	assert_same(active_camera, expedition.hero.follow_camera)
	assert_lt(
		active_camera.get_screen_center_position().distance_to(expedition.hero.global_position),
		1.0
	)
