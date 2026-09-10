extends RefCounted
class_name ExpeditionState

const DORMANT: StringName = &"dormant"
const ACTIVE: StringName = &"active"
const CLEARED: StringName = &"cleared"

var _site_states: Dictionary[StringName, StringName] = {}
var _discovered: Dictionary[StringName, bool] = {}
var _claimed_rewards: Dictionary[StringName, StringName] = {}

func register_place(id: StringName) -> void:
	if not _site_states.has(id):
		_site_states[id] = DORMANT
		_discovered[id] = false

func site_state(id: StringName) -> StringName:
	return _site_states.get(id, DORMANT)

func mark_discovered(id: StringName) -> bool:
	register_place(id)
	if _discovered[id]:
		return false
	_discovered[id] = true
	return true

func is_discovered(id: StringName) -> bool:
	return _discovered.get(id, false)

func mark_active(id: StringName) -> void:
	register_place(id)
	if _site_states[id] != CLEARED:
		_site_states[id] = ACTIVE

func mark_dormant(id: StringName) -> void:
	register_place(id)
	if _site_states[id] != CLEARED:
		_site_states[id] = DORMANT

func mark_cleared(id: StringName) -> void:
	register_place(id)
	_site_states[id] = CLEARED
	_discovered[id] = true

func is_cleared(id: StringName) -> bool:
	return site_state(id) == CLEARED

func claim_reward(site_id: StringName, reward_id: StringName) -> bool:
	if _claimed_rewards.has(site_id):
		return false
	_claimed_rewards[site_id] = reward_id
	return true

func is_reward_claimed(site_id: StringName) -> bool:
	return _claimed_rewards.has(site_id)

func reward_for(site_id: StringName) -> StringName:
	return _claimed_rewards.get(site_id, &"")
