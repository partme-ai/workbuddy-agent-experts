"""Ephemeral Blender UI shared by Managed sessions and the optional Connector.

No preferences or scene custom properties are written. Registration lasts only
for the live session and is removed on revoke, file load or shutdown.
"""
from .commands.view import ViewCommands


class Frontend:
    def __init__(self, bpy_module, runtime):
        self.bpy = bpy_module
        self.runtime = runtime
        self.classes = []
        self.header = None

    def redraw(self):
        for window in self.bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in {"VIEW_3D", "DOPESHEET_EDITOR", "PROPERTIES"}:
                    area.tag_redraw()

    def register(self):
        bpy = self.bpy
        runtime = self.runtime
        view = ViewCommands(bpy)

        class CODEXBLENDER_OT_pause_work(bpy.types.Operator):
            bl_idname = "codex_blender.pause_work"
            bl_label = "暂停 / 接管"
            bl_description = "Stop queued design commands and safely take over editing"

            def execute(self, context):
                runtime.session.pause()
                try:
                    view.set_playback({"playing": False})
                except Exception:
                    pass
                return {"FINISHED"}

        class CODEXBLENDER_OT_resume_work(bpy.types.Operator):
            bl_idname = "codex_blender.resume_work"
            bl_label = "恢复 Codex"
            bl_description = "Resume; Codex must inspect the scene before further design"

            def execute(self, context):
                runtime.session.resume_local()
                return {"FINISHED"}

        class CODEXBLENDER_OT_revoke_work(bpy.types.Operator):
            bl_idname = "codex_blender.revoke_work"
            bl_label = "撤销连接"

            def execute(self, context):
                runtime.session.revoke()
                bpy.app.timers.register(runtime.close, first_interval=0.01)
                return {"FINISHED"}

        class CODEXBLENDER_OT_change_view(bpy.types.Operator):
            bl_idname = "codex_blender.change_view"
            bl_label = "Set View"
            view: bpy.props.EnumProperty(items=[(v, v.title(), "") for v in ("CAMERA", "FRONT", "SIDE", "TOP")])

            def execute(self, context):
                try:
                    view.set_view({"view": self.view})
                except Exception as exc:
                    self.report({"WARNING"}, str(exc))
                    return {"CANCELLED"}
                return {"FINISHED"}

        class CODEXBLENDER_OT_play_work(bpy.types.Operator):
            bl_idname = "codex_blender.play_work"
            bl_label = "播放 / 暂停动画"

            def execute(self, context):
                view.set_playback({"playing": not context.screen.is_animation_playing})
                return {"FINISHED"}

        class CODEXBLENDER_OT_jump_marker(bpy.types.Operator):
            bl_idname = "codex_blender.jump_marker"
            bl_label = "Jump to Marker"
            frame: bpy.props.IntProperty()

            def execute(self, context):
                view.set_playback({"playing": False})
                view.set_frame({"frame": self.frame})
                return {"FINISHED"}

        class VIEW3D_PT_codex_session(bpy.types.Panel):
            bl_idname = "VIEW3D_PT_codex_session"
            bl_label = "Codex 制作过程"
            bl_space_type = "VIEW_3D"
            bl_region_type = "UI"
            bl_category = "Codex"

            def draw(self, context):
                layout = self.layout
                status = runtime.session.status()
                layout.label(text=status["sessionId"], icon="LINKED")
                layout.label(text="场景：" + context.scene.name)
                layout.label(text="模式：" + {"interactive":"交互审阅", "auto_with_budget":"自动制作", "review_only":"只读检查"}[status["executionPolicy"]["mode"]])
                layout.label(text="阶段：" + ("就绪" if status["stage"] == "Ready" else status["stage"]))
                if status["progress"] is not None:
                    layout.label(text=f'报告进度：{status["progress"]:.0%}')
                layout.label(text=f'场景版本 {status["sceneRevision"]} | 等待操作 {runtime.executor.pending_count}')
                if status["lastCommand"]:
                    layout.label(text="最近操作：" + status["lastCommand"])
                for name in status["changedObjects"][:4]:
                    layout.label(text=name, icon="OBJECT_DATA")
                if status["lastError"]:
                    layout.label(text=status["lastError"]["code"], icon="ERROR")
                if status["needsInspection"]:
                    layout.label(text="等待重新检查场景", icon="INFO")
                row = layout.row(align=True)
                if status["paused"]:
                    row.operator("codex_blender.resume_work", icon="PLAY")
                else:
                    row.operator("codex_blender.pause_work", icon="PAUSE")
                row.operator("codex_blender.revoke_work", text="撤销连接", icon="CANCEL")
                row = layout.row(align=True)
                for name, label in (("CAMERA", "相机"), ("FRONT", "正面"), ("SIDE", "侧面"), ("TOP", "顶面")):
                    row.operator("codex_blender.change_view", text=label).view = name
                row = layout.row(align=True)
                row.operator("codex_blender.play_work", icon="PLAY")
                row.prop(context.scene, "frame_current", text="帧")
                for marker in sorted(context.scene.timeline_markers, key=lambda m: m.frame)[:12]:
                    if context.scene.frame_start <= marker.frame <= context.scene.frame_end:
                        layout.operator("codex_blender.jump_marker", text=f'{marker.frame}: {marker.name}').frame = marker.frame

        self.classes = [CODEXBLENDER_OT_pause_work, CODEXBLENDER_OT_resume_work, CODEXBLENDER_OT_revoke_work,
                        CODEXBLENDER_OT_change_view, CODEXBLENDER_OT_play_work, CODEXBLENDER_OT_jump_marker,
                        VIEW3D_PT_codex_session]
        registered = []
        try:
            for cls in self.classes:
                bpy.utils.register_class(cls)
                registered.append(cls)
        except Exception:
            for cls in reversed(registered):
                bpy.utils.unregister_class(cls)
            self.classes = []
            raise

        def draw_header(self, context):
            status = runtime.session.status()
            row = self.layout.row(align=True)
            row.label(text="Codex: " + ("已暂停" if status["paused"] else status["stage"]))
            row.operator("codex_blender.resume_work" if status["paused"] else "codex_blender.pause_work",
                         text="恢复" if status["paused"] else "接管", icon="PLAY" if status["paused"] else "PAUSE")

        self.header = draw_header
        bpy.types.VIEW3D_HT_header.append(draw_header)
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    area.spaces.active.show_region_ui = True
        self.redraw()

    def unregister(self):
        if self.header:
            self.bpy.types.VIEW3D_HT_header.remove(self.header)
            self.header = None
        for cls in reversed(self.classes):
            self.bpy.utils.unregister_class(cls)
        self.classes = []
        self.redraw()
