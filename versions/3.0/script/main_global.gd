extends Node

signal item_list_changed
var items : Array[PackedStringArray] = []
var item_index : int = 0

func _ready() -> void:
	sys_check()

func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		get_tree().quit()

func sys_check():
	var op_sys = OS.get_name()
	if op_sys == "Windows":
		print_rich("Your Operation System: ","[color=yellow][b]"+ op_sys + "[/b][/color]")
	else:
		print_rich("Your Operation System: ","[color=blue][b]" + op_sys + "[/b][/color]")

	#await get_tree().create_timer(0.5).timeout
	var output = []
	var ffmpeg_is_working = OS.execute("ffmpeg", ["-version"], output)
	if ffmpeg_is_working == 0:
		print("FFmpeg found!")
	else:
		printerr("FFmpeg not found!")

func add_item(multi_items : PackedStringArray):
	for item in multi_items:
		items.append(multi_items)
		item_index = items.size()
		emit_signal("item_list_changed")
	#var same_multi_selected_item
	await get_tree().create_timer(0.5).timeout
	print("item index: ", item_index, "\n", "uploaded file(s): " , items)#same_multi_selected_item

func delete():
	items = []
	item_index = items.size()
	#print("item index: ", item_index, "\n", "uploaded file(s): " , items)#same_multi_selected_item
	emit_signal("item_list_changed")
