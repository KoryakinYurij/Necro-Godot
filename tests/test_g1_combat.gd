extends GutTest

const EXPEDITION_SCENE: PackedScene = preload("res://expedition/expedition.tscn")

func _spawn_expedition() -> Expedition:
	var expedition: Expedition = EXPEDITION_SCENE.instantiate() as Expedition
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

func _move_away_until_enemy_is_defeated(expedition: Expedition) -> void:
	Input.action_press(&"move_left")
	await wait_physics_frames(180)
	Input.action_release(&"move_left")
	Input.action_press(&"move_up")
	await wait_physics_frames(180)
	Input.action_release(&"move_up")
	var snapshot := expedition.combat_snapshot()
	assert_false(bool(snapshot[&"dead"]))
	assert_false(bool(snapshot[&"enemy_alive"]))
	assert_false(bool(snapshot[&"minion_has_target"]))

func test_enemy_deals_damage_through_running_combat_loop() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(50)
	var snapshot := expedition.combat_snapshot()
	assert_lt(int(snapshot[&"hero_health"]), int(snapshot[&"hero_max_health"]))

func test_autonomous_minion_acquires_and_defeats_live_enemy() -> void:
	var expedition: Expedition = _spawn_expedition()
	await _move_away_until_enemy_is_defeated(expedition)

func test_idle_combat_can_kill_player_through_running_gameplay() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(300)
	var snapshot := expedition.combat_snapshot()
	assert_true(bool(snapshot[&"dead"]))
	assert_eq(int(snapshot[&"hero_health"]), 0)

func test_repeated_death_restart_cycles_create_fresh_expeditions() -> void:
	var expedition: Expedition = _spawn_expedition()
	for expected_generation: int in range(1, 4):
		await wait_physics_frames(300)
		var dead_state := expedition.combat_snapshot()
		assert_true(bool(dead_state[&"dead"]), "generation %d should die through combat" % expected_generation)
		assert_eq(int(dead_state[&"generation"]), expected_generation)
		_press_restart()
		await wait_physics_frames(3)
		var restarted := expedition.combat_snapshot()
		assert_eq(int(restarted[&"generation"]), expected_generation + 1)
		assert_false(bool(restarted[&"dead"]))
		assert_eq(int(restarted[&"hero_health"]), int(restarted[&"hero_max_health"]))
		assert_true(bool(restarted[&"enemy_alive"]))
		var active_camera: Camera2D = expedition.get_viewport().get_camera_2d()
		assert_same(active_camera, expedition.hero.follow_camera)
		assert_lt(active_camera.get_screen_center_position().distance_to(expedition.hero.global_position), 1.0)

func test_new_minion_can_win_after_death_and_restart() -> void:
	var expedition: Expedition = _spawn_expedition()
	await wait_physics_frames(300)
	assert_true(bool(expedition.combat_snapshot()[&"dead"]))
	_press_restart()
	await wait_physics_frames(3)
	assert_eq(int(expedition.combat_snapshot()[&"generation"]), 2)
	await _move_away_until_enemy_is_defeated(expedition)
