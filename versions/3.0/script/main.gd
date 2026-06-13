extends Control
@onready var help_text: Label = $help_text
@onready var item_list: Label = $ScrollContainer/item_list
@onready var item_text: Label = $item_text


var items : Array[String] = []
var number_of_item : int
var is_convertin : bool
func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("ui_cancel"):
		get_tree().quit()
	
	

func _ready() -> void:
	help_text.visible = true
	item_list.visible = false
	item_text.visible = false
	print(number_of_item)
	get_viewport().files_dropped.connect(_on_files_dropped)
	sys_check()
	
func sys_check():
	var op_sys = OS.get_name()
	print("Your Operation System is: ", op_sys)
#	await get_tree().create_timer(0.5).timeout
	var output = []
	var code = OS.execute("ffmpeg", ["-version"], output)
	if code == 0:
		print("FFmpeg found!")
	else:
		printerr("FFmpeg not found!")
		


func _on_files_dropped(files: PackedStringArray):
	for file in files:
		check_uploaded_file(file)
		

func check_uploaded_file(file):
	items.append(file)
	number_of_item = items.size()
	print("Dropped:", file)
	print("Index: ", number_of_item,"\n","File: " ,  str(items))
	if number_of_item >= 1:
		help_text.visible = false
		item_list.visible = true
		item_text.visible = true
		item_list.text = "\n".join(items)
	else:
		help_text.visible = true
		item_text.visible = false
		item_list.visible = false
