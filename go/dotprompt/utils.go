package dotprompt

// MergeMaps merges two map[string]interface{} objects and handles nil maps.
func MergeMaps(map1, map2 map[string]interface{}) map[string]interface{} {
	// If map1 is nil, initialize it as an empty map
	if map1 == nil {
		map1 = make(map[string]interface{})
	}

	// If map2 is nil, return map1 as is
	if map2 == nil {
		return map1
	}

	// Merge map2 into map1
	for key, value := range map2 {
		map1[key] = value
	}

	return map1
}
