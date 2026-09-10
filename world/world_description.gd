extends RefCounted
class_name WorldDescription

const DEFAULT_SEED: int = 20260910
const DISCOVERY_RADIUS: float = 285.0
const ACTIVATION_RADIUS: float = 145.0
const RETREAT_RADIUS: float = 330.0

var seed: int
var _places: Dictionary[StringName, Dictionary] = {}

func _init(p_seed: int = DEFAULT_SEED) -> void:
	seed = p_seed
	for spec: Dictionary in _place_specs():
		var id := StringName(spec[&"id"])
		_places[id] = _build_place(
			id,
			StringName(spec[&"kind"]),
			String(spec[&"display_name"]),
			spec[&"anchor"]
		)

func places() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for spec: Dictionary in _place_specs():
		result.append(place(StringName(spec[&"id"])))
	return result

func place(id: StringName) -> Dictionary:
	if not _places.has(id):
		return {}
	return _places[id].duplicate(true)

func _build_place(id: StringName, kind: StringName, display_name: String, anchor: Vector2) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = _local_seed(id)
	var jitter := Vector2(rng.randi_range(-90, 90), rng.randi_range(-80, 80))
	return {
		&"id": id,
		&"kind": kind,
		&"display_name": display_name,
		&"position": anchor + jitter,
		&"discovery_radius": DISCOVERY_RADIUS,
		&"activation_radius": ACTIVATION_RADIUS,
		&"retreat_radius": RETREAT_RADIUS,
	}

func _local_seed(id: StringName) -> int:
	var normalized_seed: int = absi(seed) % 2147483647
	var mixed: int = (normalized_seed * 1103515245 + _stable_name_hash(id) * 12345 + 2654435761) & 0x7fffffff
	return maxi(mixed, 1)

func _stable_name_hash(id: StringName) -> int:
	var value: int = 2166136261
	for byte_value: int in String(id).to_utf8_buffer():
		value = ((value ^ byte_value) * 16777619) & 0x7fffffff
	return value

static func _place_specs() -> Array[Dictionary]:
	return [
		{
			&"id": &"bone_camp",
			&"kind": &"encounter",
			&"display_name": "Bone Camp",
			&"anchor": Vector2(-520.0, -235.0),
		},
		{
			&"id": &"ruins",
			&"kind": &"ruins",
			&"display_name": "Forgotten Ruins",
			&"anchor": Vector2(525.0, 250.0),
		},
	]
