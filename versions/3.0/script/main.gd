extends Control

@onready var file_dialog: FileDialog = $FileDialog
@onready var open_folder_button: Button = $Open_folder_button
@onready var item_list: Label = $ScrollContainer/item_list



func _process(_delta: float) -> void:
	
	pass

func _ready() -> void:
	MainGlobal.item_list_changed.connect(label_change)
	file_dialog.visible = false
	

func label_change():
	item_list.text = str(MainGlobal.items)
func _on_open_folder_button_pressed() -> void:
	file_dialog.visible = true
	


func _on_file_dialog_files_dropped(files: PackedStringArray) -> void:
	print("files dropped: ", files)


func _on_file_dialog_files_selected(paths: PackedStringArray) -> void:
	print("selected items: ", paths)
	MainGlobal.add_item(paths)


func _on_delete_list_pressed() -> void:
	MainGlobal.delete()
