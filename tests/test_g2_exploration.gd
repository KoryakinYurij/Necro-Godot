extends GutTest

const EXPEDITION_SCENE: PackedScene = preload("res://expedition/expedition.tscn")
const ENEMY_SCENE: PackedScene = preload("res://entities/enemy/enemy.tscn")

func _spawn_expedition(seed: int = 777) -> Expedition:
	var expedition := EXPEDITION_SCENE.instantiate() as Expedition
	assert_not_null(expedition)
	expedition.expedition_seed = seed
	add_child_autofree(expedition)
	return expedition

func _site_snapshot(expedition: Expedition, site_id: StringName) -> Dictionary:
	var sites: Dictionary = expedition.exploration_snapshot()[&"sites"]
	return sites[site_id]

func _enter_site(expedition: Expedition, site_id: StringName) -> EncounterSite:
	var site := expedition.get_site(site_id)
	assert_not_null(site)
	expedition.hero.global_position = site.global_position
	return site

func _kill_site_enemies(site: EncounterSite) -> void:
	for enemy: Enemy in site.active_enemies():
		enemy.receive_damage(999)

func test_world_description_is_seeded_stable_and_visit_order_independent() -> void:
	var first := WorldDescription.new(123456)
	var second := WorldDescription.new(123456)
	var different := WorldDescription.new(123457)
	var first_ruins := first.place(&"ruins")
	var first_camp := first.place(&"bone_camp")
	var second_camp := second.place(&"bone_camp")
	var second_ruins := second.place(&"ruins")
	assert_eq(first_camp[&"position"], second_camp[&"position"])
	assert_eq(first_ruins[&"position"], second_ruins[&"position"])
	assert_ne(first_camp[&"position"], different.place(&"bone_camp")[&"position"])
	assert_ne(first_ruins[&"position"], different.place(&"ruins")[&"position"])

func test_encounter_can_be_bypassed_retreat_reentered_without_duplicates_or_stale_spawn() -> void:
	var expedition := _spawn_expedition()
	var camp := expedition.get_site(&"bone_camp")
	assert_not_null(camp)
	expedition.hero.global_position = camp.global_position + Vector2(camp.activation_radius + 45.0, 0.0)
	await wait_physics_frames(4)
	assert_eq(int(_site_snapshot(expedition, &"bone_camp")[&"live_enemy_count"]), 0)

	_enter_site(expedition, &"bone_camp")
	await wait_physics_frames(2)
	var first_activation := _site_snapshot(expedition, &"bone_camp")
	assert_true(bool(first_activation[&"active"]))
	assert_eq(int(first_activation[&"live_enemy_count"]), 1)
	assert_true(bool(first_activation[&"pending_spawn"]))

	expedition.hero.global_position = camp.global_position + Vector2(camp.retreat_radius + 35.0, 0.0)
	await wait_physics_frames(3)
	var retreated := _site_snapshot(expedition, &"bone_camp")
	assert_false(bool(retreated[&"active"]))
	assert_eq(int(retreated[&"live_enemy_count"]), 0)
	assert_false(bool(retreated[&"pending_spawn"]))
	await wait_physics_frames(40)
	assert_eq(
		int(_site_snapshot(expedition, &"bone_camp")[&"live_enemy_count"]),
		0,
		"obsolete delayed spawn must be harmless"
	)

	_enter_site(expedition, &"bone_camp")
	await wait_physics_frames(40)
	var reentered := _site_snapshot(expedition, &"bone_camp")
	assert_true(bool(reentered[&"active"]))
	assert_eq(int(reentered[&"live_enemy_count"]), 2)
	assert_false(bool(reentered[&"pending_spawn"]))
	await wait_physics_frames(20)
	assert_lte(int(_site_snapshot(expedition, &"bone_camp")[&"live_enemy_count"]), 2)

func test_minion_targets_only_active_local_encounter_enemies() -> void:
	var expedition := _spawn_expedition()
	var camp := _enter_site(expedition, &"bone_camp")
	var unrelated := ENEMY_SCENE.instantiate() as Enemy
	assert_not_null(unrelated)
	unrelated.global_position = Vector2(980.0, 620.0)
	add_child_autofree(unrelated)
	unrelated.set_target(expedition.hero)
	await wait_physics_frames(15)
	assert_true(expedition.minion.has_live_target())
	assert_true(camp.active_enemies().has(expedition.minion.target))
	assert_ne(expedition.minion.target, unrelated)

func test_minion_can_kill_final_local_enemy_without_stale_target_race() -> void:
	var expedition := _spawn_expedition()
	var camp := _enter_site(expedition, &"bone_camp")
	await wait_physics_frames(40)
	var enemies := camp.active_enemies()
	assert_eq(enemies.size(), 2)
	enemies[0].receive_damage(999)
	var final_enemy: Enemy = enemies[1]
	final_enemy.receive_damage(final_enemy.get_health() - expedition.minion.attack_damage)
	expedition.minion.global_position = final_enemy.global_position
	await wait_physics_frames(8)
	assert_true(camp.is_cleared())
	assert_false(expedition.minion.has_live_target())
	assert_null(expedition.minion.combat_site)

func test_cleared_encounter_is_terminal_for_the_expedition() -> void:
	var expedition := _spawn_expedition()
	var camp := _enter_site(expedition, &"bone_camp")
	await wait_physics_frames(40)
	_kill_site_enemies(camp)
	await wait_physics_frames(3)
	assert_true(camp.is_cleared())
	assert_eq(int(camp.snapshot()[&"live_enemy_count"]), 0)
	expedition.hero.global_position = camp.global_position + Vector2(camp.retreat_radius + 40.0, 0.0)
	await wait_physics_frames(4)
	expedition.hero.global_position = camp.global_position
	await wait_physics_frames(40)
	assert_true(camp.is_cleared())
	assert_eq(int(camp.snapshot()[&"live_enemy_count"]), 0)

func test_ruins_reward_pauses_applies_once_and_restart_invalidates_run_state() -> void:
	var expedition := _spawn_expedition(991)
	var ruins := _enter_site(expedition, &"ruins")
	await wait_physics_frames(40)
	_kill_site_enemies(ruins)
	await get_tree().process_frame
	await get_tree().process_frame
	var offered := expedition.exploration_snapshot()
	assert_true(ruins.is_cleared())
	assert_eq(StringName(offered[&"modal_owner"]), &"ruins_reward")
	assert_true(bool(offered[&"tree_paused"]))
	var before_max := int(offered[&"hero_max_health"])
	assert_true(expedition.choose_reward(&"vigor"))
	assert_false(
		expedition.choose_reward(&"vigor"),
		"repeated reward input must not apply twice"
	)
	var claimed := expedition.exploration_snapshot()
	assert_false(bool(claimed[&"tree_paused"]))
	assert_eq(int(claimed[&"hero_max_health"]), before_max + 30)
	assert_eq(StringName(claimed[&"ruins_reward"]), &"vigor")

	expedition.restart_expedition()
	await wait_physics_frames(3)
	var restarted := expedition.exploration_snapshot()
	assert_eq(int(restarted[&"generation"]), 2)
	assert_eq(int(restarted[&"hero_max_health"]), 100)
	assert_eq(StringName(restarted[&"ruins_reward"]), &"")
	var restarted_sites: Dictionary = restarted[&"sites"]
	var restarted_ruins: Dictionary = restarted_sites[&"ruins"]
	assert_false(bool(restarted_ruins[&"cleared"]))
	assert_eq(int(restarted_ruins[&"live_enemy_count"]), 0)

func test_restart_cancels_old_activation_work() -> void:
	var expedition := _spawn_expedition()
	_enter_site(expedition, &"bone_camp")
	await wait_physics_frames(2)
	assert_true(bool(_site_snapshot(expedition, &"bone_camp")[&"pending_spawn"]))
	expedition.restart_expedition()
	await wait_physics_frames(40)
	var camp := _site_snapshot(expedition, &"bone_camp")
	assert_false(bool(camp[&"active"]))
	assert_eq(int(camp[&"live_enemy_count"]), 0)
	assert_false(bool(camp[&"pending_spawn"]))
