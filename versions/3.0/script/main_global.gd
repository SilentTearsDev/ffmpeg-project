extends Node

var items : Array[String] = []
var item_index : int = 0

func _ready() -> void:
	sys_check()

func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		get_tree().quit()

func sys_check():
	var op_sys = OS.get_name()
	print("Your Operation System is: ", op_sys)
	#await get_tree().create_timer(0.5).timeout
	var output = []
	var ffmpeg_is_working = OS.execute("ffmpeg", ["-version"], output)
	if ffmpeg_is_working == 0:
		print("FFmpeg found!")
	else:
		printerr("FFmpeg not found!")

func add_item(multi_items : PackedStringArray):
	for item in multi_items:
		items.append(str(multi_items).get_file())
		item_index = items.size()
	#var same_multi_selected_item
	await get_tree().create_timer(0.5).timeout
	print("item index: ", item_index, " uploaded file(s): " ,  items)#same_multi_selected_item
