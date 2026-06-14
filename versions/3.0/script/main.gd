extends Control

@onready var file_dialog: FileDialog = $FileDialog
@onready var open_folder_button: Button = $Open_folder_button


func _ready() -> void:
	file_dialog.visible = false
	

func _on_open_folder_button_pressed() -> void:
	file_dialog.visible = true
	


func _on_file_dialog_files_dropped(files: PackedStringArray) -> void:
	print("files dropped: ", files)


func _on_file_dialog_files_selected(paths: PackedStringArray) -> void:
	print("selected items: ", paths)
	MainGlobal.add_item(paths)
