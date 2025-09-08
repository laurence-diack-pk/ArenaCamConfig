#!/usr/bin/env python3
"""
Camera Configuration GUI using Textual
Provides a tree-based interface for editing ArenaSDK camera parameters with proper modal dialogs
"""

import socket
import struct
import time
import traceback
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Tree, Header, Footer, Static, Input, Select, Button, RadioSet, RadioButton
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import events, log
from textual.reactive import reactive

from arena_api.system import system
from arena_api import enums

@dataclass
class CameraNode:
    """Represents a camera configuration node"""
    name: str
    display_name: str
    node_obj: Any
    is_category: bool = False
    is_writable: bool = False
    is_readable: bool = False
    is_executable: bool = False
    node_type: str = ""
    value: str = ""
    enum_values: List[str] = None
    min_val: Any = None
    max_val: Any = None
    increment: Any = None
    unit: str = ""

class DeviceSelectionScreen(ModalScreen):
    """Modal for selecting camera device"""
    
    def __init__(self, devices):
        super().__init__()
        self.devices = devices
        self.device_options = []
        self.result = None
        self._prepare_device_options()
    
    def _prepare_device_options(self):
        """Extract device info for display"""
        for i, device in enumerate(self.devices):
            try:
                # Try to get device info
                family_name = "Unknown"
                model_name = "Unknown"
                ip_str = "Unknown"
                
                try:
                    # Try to access device info directly
                    family_name = device.nodemap.get_node('DeviceFamilyName').value
                    model_name = device.nodemap.get_node('DeviceModelName').value
                except:
                    # Fallback to any available attributes
                    family_name = getattr(device, 'device_family_name', 'Unknown')
                    model_name = getattr(device, 'device_model_name', 'Unknown')
                
                try:
                    # Try to get IP address
                    ip_int = device.tl_device_nodemap.get_node('GevDeviceIPAddress').value
                    ip_str = socket.inet_ntoa(struct.pack('!I', ip_int))
                except:
                    ip_str = 'Unknown'
                
                display_text = f"{family_name} {model_name} - {ip_str}"
                self.device_options.append((display_text, i))
            except:
                # Fallback if device info not accessible
                self.device_options.append((f"Device {i+1}", i))
    
    def compose(self) -> ComposeResult:
        with Container(id="device-dialog"):
            yield Static("Select Camera Device", id="device-title")
            
            if not self.device_options:
                yield Static("No devices found", id="device-info")
                with Horizontal():
                    yield Button("Refresh", variant="primary", id="refresh")
            else:
                # Set first device as default selection
                yield Select(self.device_options, value=self.device_options[0][1], id="device-select")
                with Horizontal():
                    yield Button("Connect", variant="success", id="connect")
                    yield Button("Refresh", variant="primary", id="refresh") 
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "connect":
            if self.device_options:
                try:
                    select_widget = self.query_one("#device-select", Select)
                    if select_widget.value is not None:
                        device_index = select_widget.value
                        self.result = self.devices[device_index]
                        self.dismiss(self.result)
                    else:
                        self.app.notify("Please select a device", severity="warning")
                except:
                    self.app.notify("Please select a device", severity="warning")
        elif event.button.id == "refresh":
            self.result = "refresh"
            self.dismiss(self.result)


class ExecuteScreen(ModalScreen):
    """Simple modal for executing commands"""
    
    def __init__(self, camera_node: CameraNode):
        super().__init__()
        self.camera_node = camera_node
        self.result = None
    
    def compose(self) -> ComposeResult:
        with Container(id="execute-dialog"):
            yield Static(f"Execute: {self.camera_node.display_name}", id="execute-title")
            yield Static(f"Command: {self.camera_node.display_name}", id="execute-info")
            
            with Horizontal():
                yield Button("Execute", variant="success", id="execute")
                yield Button("Cancel", variant="error", id="cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "execute":
            try:
                # Execute the camera node command
                self.camera_node.node_obj.execute()
                self.result = True
                self.dismiss(self.result)
            except Exception as e:
                self.app.notify(f"Execution failed: {str(e)}", severity="error")
                self.result = False
                self.dismiss(self.result)
        else:
            self.dismiss(None)


class EditValueScreen(ModalScreen):
    """Simple modal for editing values"""
    
    def __init__(self, camera_node: CameraNode):
        super().__init__()
        self.camera_node = camera_node
        self.result = None
    
    def compose(self) -> ComposeResult:
        with Container(id="edit-dialog"):
            yield Static(f"Edit: {self.camera_node.display_name}", id="edit-title")
            yield Static(f"Type: {self.camera_node.node_type} | Current: {self.camera_node.value}", id="edit-info")
            
            # Show appropriate input widget based on type
            if self.camera_node.enum_values:
                with RadioSet(id="value-radio"):
                    for value in self.camera_node.enum_values:
                        is_current = str(self.camera_node.value) == str(value)
                        yield RadioButton(value, value=is_current, id=f"radio-{value}")
            elif self.camera_node.node_type == "Boolean":
                with RadioSet(id="value-radio"):
                    current_bool = str(self.camera_node.value).lower() == "true"
                    yield RadioButton("True", value=current_bool, id="radio-True")
                    yield RadioButton("False", value=not current_bool, id="radio-False")
            else:
                yield Input(value=str(self.camera_node.value), id="value-input")
            
            with Horizontal():
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="error", id="cancel")
    
    def on_mount(self) -> None:
        """Set focus to the currently selected option"""
        if self.camera_node.enum_values or self.camera_node.node_type == "Boolean":
            try:
                radio_set = self.query_one("#value-radio", RadioSet)
                # Find and focus the currently selected radio button
                for button in radio_set.query(RadioButton):
                    if button.value:  # This is the selected one
                        button.focus()
                        break
            except:
                pass
        else:
            # Focus the input field for text/number inputs
            try:
                input_widget = self.query_one("#value-input", Input)
                input_widget.focus()
            except:
                pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            try:
                if self.camera_node.enum_values or self.camera_node.node_type == "Boolean":
                    radio_set = self.query_one("#value-radio", RadioSet)
                    if radio_set.pressed_button:
                        self.result = radio_set.pressed_button.label.plain
                        if self.camera_node.node_type == "Boolean":
                            self.result = self.result == "True"
                else:
                    input_widget = self.query_one("#value-input", Input)
                    value = input_widget.value
                    
                    if self.camera_node.node_type == "Integer":
                        self.result = int(value)
                        if self.camera_node.min_val is not None and self.result < self.camera_node.min_val:
                            raise ValueError(f"Below minimum ({self.camera_node.min_val})")
                        if self.camera_node.max_val is not None and self.result > self.camera_node.max_val:
                            raise ValueError(f"Above maximum ({self.camera_node.max_val})")
                    elif self.camera_node.node_type == "Float":
                        self.result = float(value)
                        if self.camera_node.min_val is not None and self.result < self.camera_node.min_val:
                            raise ValueError(f"Below minimum ({self.camera_node.min_val})")
                        if self.camera_node.max_val is not None and self.result > self.camera_node.max_val:
                            raise ValueError(f"Above maximum ({self.camera_node.max_val})")
                    else:
                        self.result = value
                
                self.dismiss(self.result)
            except ValueError as e:
                self.app.notify(f"Invalid value: {str(e)}", severity="error")
        else:
            self.dismiss(None)


class CameraConfigApp(App):
    """Main camera configuration application"""
    
    CSS = """
    #edit-dialog, #execute-dialog, #device-dialog {
        align: center middle;
        width: 50;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 2;
        margin: 4;
    }
    
    #device-dialog {
        width: 60;
    }
    
    #edit-title, #execute-title, #device-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    #edit-info, #execute-info, #device-info {
        margin-bottom: 1;
        text-align: center;
    }
    
    #value-input, #value-radio, #device-select {
        margin-bottom: 1;
    }
    
    Tree {
        scrollbar-background: $panel;
        scrollbar-color: $accent;
        display: none;
    }
    
    Tree.connected {
        display: block;
    }
    
    #status-bar {
        dock: bottom;
        height: 2;
        background: $panel;
        color: $text;
        padding: 0 1;
    }
    
    #header-bar {
        dock: top;
        height: 1;
        text-style: bold;
        background: $accent;
        color: black;
        padding: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "switch_nodemap", "Switch Nodemap"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    current_nodemap = reactive(0)
    status_message = reactive("Scanning for cameras...")
    
    def __init__(self):
        super().__init__()
        self.device = None
        self.device_info = {}
        self.theme = "textual-dark"
        self.nodemap_names = [
            "Device", "TL Device", "TL Stream", "TL Interface", "TL System"
        ]
        self.tree_nodes: Dict[str, CameraNode] = {}
        self.expanded_nodes: set = set()  # Track expanded nodes
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Scanning for cameras...", id="header-bar")
        with Container():
            yield Tree("Camera Configuration", id="config-tree")
        yield Static(self.status_message, id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application"""
        # Don't expand tree until we have a camera connection
        # Wait a brief moment for UI to fully render, then start connection
        self.set_timer(0.05, self.initialize_camera)
    
    def watch_status_message(self, new_message: str) -> None:
        """Update status bar when message changes"""
        try:
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(new_message)
        except:
            # Widget not mounted yet
            pass
    
    def update_status(self, message: str) -> None:
        """Safely update the status message"""
        self.status_message = message
        try:
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(message)
        except:
            # Widget not mounted yet, reactive will handle it
            pass
    
    async def initialize_camera(self) -> None:
        """Initialize camera connection"""
        try:
            # Ensure UI is ready and show connecting status
            header_bar = self.query_one("#header-bar", Static)
            header_bar.update("Scanning for cameras...")
            self.update_status("Scanning for cameras...")
            
            # Start device selection process
            self.start_device_selection()
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
    
    def start_device_selection(self) -> None:
        """Start the device selection process"""
        while True:
            devices = system.create_device()
            
            if not devices:
                self.update_status("No devices found")
                header_bar = self.query_one("#header-bar", Static)
                header_bar.update("No cameras found")
                return
            
            # Show device selection screen
            self.update_status(f"Found {len(devices)} camera(s)")
            self.push_screen(DeviceSelectionScreen(devices), self.handle_device_selection)
            break  # Exit the loop, callback will handle the rest
    
    def handle_device_selection(self, result) -> None:
        """Handle device selection result"""
        if result == "refresh":
            # User clicked refresh, rescan devices
            self.update_status("Rescanning for devices...")
            self.start_device_selection()
        elif result is None:
            # User cancelled
            self.update_status("Device selection cancelled")
            header_bar = self.query_one("#header-bar", Static)
            header_bar.update("Camera connection cancelled")
        else:
            # User selected a device
            self.device = result
            self.update_status("Connecting to selected camera...")
            self.call_later(self.continue_initialization)
    
    async def continue_initialization(self) -> None:
        """Continue initialization after device selection"""
        try:
            self.update_status("Building configuration tree...")
            await self.build_tree()

            # Update header with device info after everything is ready
            header_bar = self.query_one("#header-bar", Static)
            header_bar.update(f"Camera Config - {self.device_info['family_name']} {self.device_info['model_name']} - IP: {self.device_info['ip']} - SN: {self.device_info['serial_number']} - {self.nodemap_names[self.current_nodemap]}")
            self.update_status("Ready - Use Enter to edit values, Tab to switch nodemaps")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            header_bar = self.query_one("#header-bar", Static)
            header_bar.update("Camera initialization failed")
    
    def get_node_type_string(self, node) -> str:
        """Get human-readable node type string"""
        type_map = {
            2: "Integer",
            3: "Boolean", 
            5: "Float",
            6: "String",
            7: "Register",
            8: "Category",
            9: "Enumeration"
        }
        return type_map.get(node.interface_type.value, "Unknown")
    
    def get_node_value_string(self, node) -> str:
        """Get formatted value string for display"""
        try:
            if not node.is_readable:
                return "[Not Readable]"
            
            if node.interface_type.value in [7, 8]:  # Register or Category
                return ""
            
            value = str(node.value)
            if len(value) > 30:
                return value[:27] + "..."
            return value
        except:
            return "[Error]"
    
    def create_camera_node(self, arena_node, nodemap) -> CameraNode:
        """Create a CameraNode from an ArenaSDK node"""
        # Get enum values for enumeration nodes
        enum_values = None
        if arena_node.interface_type.value == 9:  # Enumeration
            try:
                enum_values = list(arena_node.enumentry_names)
            except:
                pass
        
        # Get min/max values
        min_val = None
        max_val = None
        increment = None
        unit = ""
        
        try:
            if hasattr(arena_node, 'min'):
                min_val = arena_node.min
            if hasattr(arena_node, 'max'):
                max_val = arena_node.max
            if hasattr(arena_node, 'inc'):
                increment = arena_node.inc
            if hasattr(arena_node, 'unit'):
                unit = arena_node.unit
        except:
            pass
        
        return CameraNode(
            name=arena_node.name,
            display_name=arena_node.display_name,
            node_obj=arena_node,
            is_category=arena_node.interface_type.value == 8,
            is_readable=arena_node.is_readable,
            is_writable=arena_node.is_writable and arena_node.interface_type.value != enums.InterfaceType.COMMAND.value,
            is_executable=arena_node.is_writable and arena_node.interface_type.value == enums.InterfaceType.COMMAND.value,
            node_type=self.get_node_type_string(arena_node),
            value=self.get_node_value_string(arena_node),
            enum_values=enum_values,
            min_val=min_val,
            max_val=max_val,
            increment=increment,
            unit=unit
        )
    
    def extract_device_info(self) -> None:
        """Extract and cache device information once after connection"""
        log()
        if not self.device:
            return
            
        try:
            ip_int = self.device.tl_device_nodemap.get_node('GevDeviceIPAddress').value
            ip_str = socket.inet_ntoa(struct.pack('!I', ip_int))


            self.device_info = {
                "family_name": self.device.nodemap.get_node('DeviceFamilyName').value,
                "model_name": self.device.nodemap.get_node('DeviceModelName').value,
                "serial_number": self.device.nodemap.get_node('DeviceSerialNumber').value,
                "ip": ip_str
            }
            
        except Exception as e:
            self.device_info = {
                "family_name": "Unknown",
                "model_name": "Unknown", 
                "serial_number": "Unknown",
                "ip": "Unknown"
            }
            log(f"Error extracting device info: {str(e)}")

    async def build_tree(self) -> None:
        """Build the tree structure from camera nodes"""
        if not self.device:
            return
        
        # Get tree and set it up for first time if needed
        tree = self.query_one("#config-tree", Tree)
        
        # Show the tree now that we have a connection
        tree.add_class("connected")
        
        if not tree.root.is_expanded:
            tree.root.expand()
        
        # Save current expanded state
        tree.root.label = f"{self.nodemap_names[self.current_nodemap]}"
        self.save_expanded_state(tree.root)
        
        # Get the appropriate nodemap
        nodemaps = [
            self.device.nodemap,
            self.device.tl_device_nodemap, 
            self.device.tl_stream_nodemap,
            self.device.tl_interface_nodemap,
            system.tl_system_nodemap
        ]
        
        nodemap = nodemaps[self.current_nodemap]
        
        # Clear existing tree
        tree.clear()
        self.tree_nodes.clear()
        
        try:
            root_node = nodemap.get_node("Root")
            if root_node and hasattr(root_node, 'features'):
                # Add root's children directly (skip showing Root)
                for child_name in root_node.features:
                    try:
                        child_arena_node = nodemap.get_node(child_name)
                        if child_arena_node:
                            await self.add_node_to_tree(child_arena_node, nodemap, tree.root)
                    except Exception as e:
                        # Skip nodes that can't be accessed
                        continue
                        
                # Restore expanded state
                self.restore_expanded_state(tree.root)
        except Exception as e:
            self.update_status(f"Error building tree: {str(e)}")

        if self.device_info == {}:
            self.extract_device_info()
    
    def save_expanded_state(self, tree_node) -> None:
        """Recursively save expanded state of tree nodes"""
        if tree_node.data and tree_node.is_expanded:
            self.expanded_nodes.add(tree_node.data.name)
        
        for child in tree_node.children:
            self.save_expanded_state(child)
    
    def restore_expanded_state(self, tree_node) -> None:
        """Recursively restore expanded state of tree nodes"""
        if tree_node.data and tree_node.data.name in self.expanded_nodes:
            tree_node.expand()
        
        for child in tree_node.children:
            self.restore_expanded_state(child)
    
    async def add_node_to_tree(self, arena_node, nodemap, parent_tree_node) -> None:
        """Recursively add a node and its children to the tree"""
        try:
            # Create our camera node wrapper
            camera_node = self.create_camera_node(arena_node, nodemap)
            
            # Create display text
            if camera_node.is_category:
                display_text = f"{camera_node.display_name}"
            elif camera_node.is_writable:
                display_text = f"[bold yellow]🔧 {camera_node.display_name}: {camera_node.value}[/bold yellow]"
            elif camera_node.is_executable:
                display_text = f"[bold green]🚀 {camera_node.display_name}[/bold green]"
            else:
                display_text = f"   {camera_node.display_name}: {camera_node.value}"
            
            # Check if this node has children
            has_children = False
            children = []
            if camera_node.is_category and hasattr(arena_node, 'features'):
                try:
                    for child_name in arena_node.features:
                        try:
                            child_arena_node = nodemap.get_node(child_name)
                            if child_arena_node:
                                children.append((child_name, child_arena_node))
                                has_children = True
                        except:
                            continue
                except:
                    pass
            
            # Add to tree - allow expansion only if it has children
            tree_node = parent_tree_node.add(display_text, data=camera_node, allow_expand=has_children)
            
            # Store reference
            self.tree_nodes[camera_node.name] = camera_node
            
            # Add children
            for child_name, child_arena_node in children:
                await self.add_node_to_tree(child_arena_node, nodemap, tree_node)
                    
        except Exception as e:
            # Skip nodes that cause errors
            pass
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection - activate editable/executable nodes"""
        if event.node.data:
            camera_node: CameraNode = event.node.data
            if camera_node.is_writable and not camera_node.is_category:
                # Open edit modal immediately on click
                self.activate_node(camera_node)
            elif camera_node.is_executable:
                # Open execute modal immediately on click
                self.activate_node(camera_node)
            else:
                # Show info in status for non-editable nodes
                info_parts = [
                    f"{camera_node.display_name}: {camera_node.value} [{camera_node.node_type}]"
                ]
                if camera_node.min_val is not None and camera_node.max_val is not None:
                    info_parts.append(f"Range: {camera_node.min_val}-{camera_node.max_val}")
                if camera_node.enum_values:
                    info_parts.append(f"Options: {', '.join(camera_node.enum_values)}")
                
                self.update_status(" | ".join(info_parts))
    
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node highlighting"""
        if event.node.data:
            camera_node: CameraNode = event.node.data
            if camera_node.is_writable and not camera_node.is_category:
                self.update_status(f"Selected: {camera_node.display_name} [{camera_node.node_type}] = {camera_node.value} - Click or Enter to edit")
            elif camera_node.is_executable:
                self.update_status(f"Selected: {camera_node.display_name} - Click or Enter to execute")
            else:
                self.update_status(f"Selected: {camera_node.display_name} [{camera_node.node_type}] = {camera_node.value} - Click or Enter for info")
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses"""
        if event.key == "enter":
            tree = self.query_one("#config-tree", Tree)
            if tree.cursor_node and tree.cursor_node.data:
                self.activate_node(tree.cursor_node.data)
        elif event.key == "tab":
            # Explicit tab handling to ensure it works
            self.action_switch_nodemap()
            event.prevent_default()
    
    def activate_node(self, camera_node: CameraNode) -> None:
        """Activate a node (open appropriate interface)"""
        if camera_node.is_writable and not camera_node.is_category:
            # Open edit modal
            self.push_screen(EditValueScreen(camera_node), self.handle_edit_result)
        elif camera_node.is_executable:
            # Open execute modal
            self.push_screen(ExecuteScreen(camera_node), self.handle_execute_result)
        else:
            # For info, just show in status
            info_parts = [
                f"{camera_node.display_name}: {camera_node.value} [{camera_node.node_type}]"
            ]
            if camera_node.min_val is not None and camera_node.max_val is not None:
                info_parts.append(f"Range: {camera_node.min_val}-{camera_node.max_val}")
            if camera_node.enum_values:
                info_parts.append(f"Options: {', '.join(camera_node.enum_values)}")
            
            self.update_status(" | ".join(info_parts))
    
    def handle_edit_result(self, result) -> None:
        """Handle the result from the edit modal"""
        if result is not None:
            tree = self.query_one("#config-tree", Tree)
            if tree.cursor_node and tree.cursor_node.data:
                camera_node = tree.cursor_node.data
                self.save_node_value(camera_node, result)
    
    def handle_execute_result(self, result) -> None:
        """Handle the result from the execute modal"""
        if result is True:
            self.update_status("Command executed successfully")
            # Refresh tree to show any updated values (without restoring selection)
            self.call_later(self.refresh_tree_no_selection)
        elif result is False:
            self.update_status("Command execution failed")
        # If result is None, user cancelled - no action needed
    
    def save_node_value(self, camera_node: CameraNode, new_value) -> None:
        """Save a new value to a camera node"""
        try:
            # Set the value on the actual Arena node
            camera_node.node_obj.value = new_value
            
            # Update our cached value
            camera_node.value = self.get_node_value_string(camera_node.node_obj)
            
            self.update_status(f"Updated {camera_node.display_name} = {camera_node.value}")
            
            # Refresh the tree to show updated dependent values (without restoring selection)
            self.call_later(self.refresh_tree_no_selection)
            
        except Exception as e:
            self.notify(f"Failed to set value: {str(e)}", severity="error")
    
    async def refresh_tree(self) -> None:
        """Refresh the tree structure after a value change"""
        try:
            # Remember current selection
            tree = self.query_one("#config-tree", Tree)
            selected_node_name = None
            if tree.cursor_node and tree.cursor_node.data:
                selected_node_name = tree.cursor_node.data.name
            
            # Rebuild tree (this preserves expanded state automatically now)
            await self.build_tree()
            
            # Try to restore selection
            if selected_node_name:
                self.restore_tree_selection(tree.root, selected_node_name)
                
        except Exception as e:
            self.update_status(f"Error refreshing tree: {str(e)}")
    
    async def refresh_tree_no_selection(self) -> None:
        """Refresh the tree structure without restoring selection (used after saves)"""
        try:
            # Rebuild tree (this preserves expanded state automatically now)
            await self.build_tree()
                
        except Exception as e:
            self.update_status(f"Error refreshing tree: {str(e)}")
    
    def restore_tree_selection(self, tree_node, target_name: str) -> bool:
        """Recursively try to restore tree selection"""
        if tree_node.data and tree_node.data.name == target_name:
            tree = self.query_one("#config-tree", Tree)
            tree.select_node(tree_node)
            return True
        
        for child in tree_node.children:
            if self.restore_tree_selection(child, target_name):
                return True
        
        return False
    
    def action_switch_nodemap(self) -> None:
        """Switch to the next nodemap"""
        self.current_nodemap = (self.current_nodemap + 1) % len(self.nodemap_names)
        self.update_status(f"Switched to {self.nodemap_names[self.current_nodemap]} nodemap")
        
        # Update header to show current nodemap
        if self.device_info:
            header_bar = self.query_one("#header-bar", Static)
            header_bar.update(f"Camera Config - {self.device_info['family_name']} {self.device_info['model_name']} - IP: {self.device_info['ip']} - SN: {self.device_info['serial_number']} - {self.nodemap_names[self.current_nodemap]}")
        
        self.call_later(self.build_tree)
    
    def action_refresh(self) -> None:
        """Refresh the current tree"""
        self.update_status("Refreshing tree...")
        self.call_later(self.build_tree)
    
    def action_quit(self) -> None:
        """Quit the application"""
        if self.device:
            try:
                system.destroy_device()
            except:
                pass
        self.exit()


def main():
    """Main entry point"""
    try:
        app = CameraConfigApp()
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            system.destroy_device()
        except:
            pass


if __name__ == "__main__":
    main()
