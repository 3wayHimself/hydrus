import ClientConstants as CC
import ClientData
import ClientGUICommon
import ClientGUIControls
import ClientGUIDialogs
import ClientGUIScrolledPanels
import ClientGUITopLevelWindows
import ClientThreading
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals as HG
import os
import sys
import traceback
import wx

class PopupWindow( wx.Window ):
    
    def __init__( self, parent ):
        
        wx.Window.__init__( self, parent, style = wx.BORDER_SIMPLE )
        
        self.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        
    
    def TryToDismiss( self ):
        
        self.GetParent().Dismiss( self )
        
    
    def EventDismiss( self, event ):
        
        self.TryToDismiss()
        
    
class PopupDismissAll( PopupWindow ):
    
    def __init__( self, parent ):
        
        PopupWindow.__init__( self, parent )
        
        hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        self._text = ClientGUICommon.BetterStaticText( self )
        self._text.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        
        button = wx.Button( self, label = 'dismiss all' )
        button.Bind( wx.EVT_BUTTON, self.EventButton )
        button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        
        hbox.Add( self._text, CC.FLAGS_VCENTER )
        hbox.Add( ( 20, 20 ), CC.FLAGS_EXPAND_BOTH_WAYS )
        hbox.Add( button, CC.FLAGS_VCENTER )
        
        self.SetSizer( hbox )
        
    
    def TryToDismiss( self ):
        
        pass
        
    
    def EventButton( self, event ):
        
        self.GetParent().DismissAll()
        
    
    def SetNumMessages( self, num_messages_pending ):
        
        self._text.SetLabelText( HydrusData.ToHumanInt( num_messages_pending ) + ' more messages' )
        
    
class PopupMessage( PopupWindow ):
    
    TEXT_CUTOFF = 1024
    
    def __init__( self, parent, job_key ):
        
        PopupWindow.__init__( self, parent )
        
        self._job_key = job_key
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        self._title = ClientGUICommon.BetterStaticText( self, style = wx.ALIGN_CENTER )
        
        popup_message_character_width = HG.client_controller.new_options.GetInteger( 'popup_message_character_width' )
        
        wrap_width = ClientGUICommon.ConvertTextToPixelWidth( self._title, popup_message_character_width )
        
        if HG.client_controller.new_options.GetBoolean( 'popup_message_force_min_width' ):
            
            self.SetMinClientSize( ( wrap_width, -1 ) )
            
        
        self._title.SetWrapWidth( wrap_width )
        self._title.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._title.Hide()
        
        self._text_1 = ClientGUICommon.BetterStaticText( self )
        self._text_1.SetWrapWidth( wrap_width )
        self._text_1.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._text_1.Hide()
        
        self._gauge_1 = ClientGUICommon.Gauge( self, size = ( wrap_width, -1 ) )
        self._gauge_1.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._gauge_1.Hide()
        
        self._text_2 = ClientGUICommon.BetterStaticText( self )
        self._text_2.SetWrapWidth( wrap_width )
        self._text_2.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._text_2.Hide()
        
        self._gauge_2 = ClientGUICommon.Gauge( self, size = ( wrap_width, -1 ) )
        self._gauge_2.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._gauge_2.Hide()
        
        self._text_yes_no = ClientGUICommon.BetterStaticText( self )
        self._text_yes_no.SetWrapWidth( wrap_width )
        self._text_yes_no.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._text_yes_no.Hide()
        
        self._yes = ClientGUICommon.BetterButton( self, 'yes', self._YesButton )
        self._yes.Hide()
        
        self._no = ClientGUICommon.BetterButton( self, 'no', self._NoButton )
        self._no.Hide()
        
        self._network_job_ctrl = ClientGUIControls.NetworkJobControl( self )
        self._network_job_ctrl.Hide()
        
        self._copy_to_clipboard_button = ClientGUICommon.BetterButton( self, 'copy to clipboard', self.CopyToClipboard )
        self._copy_to_clipboard_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._copy_to_clipboard_button.Hide()
        
        self._show_files_button = ClientGUICommon.BetterButton( self, 'show files', self.ShowFiles )
        self._show_files_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._show_files_button.Hide()
        
        self._show_tb_button = ClientGUICommon.BetterButton( self, 'show traceback', self.ShowTB )
        self._show_tb_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._show_tb_button.Hide()
        
        self._tb_text = ClientGUICommon.BetterStaticText( self )
        self._tb_text.SetWrapWidth( wrap_width )
        self._tb_text.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._tb_text.Hide()
        
        self._copy_tb_button = ClientGUICommon.BetterButton( self, 'copy traceback information', self.CopyTB )
        self._copy_tb_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._copy_tb_button.Hide()
        
        self._pause_button = ClientGUICommon.BetterBitmapButton( self, CC.GlobalBMPs.pause, self.PausePlay )
        self._pause_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._pause_button.Hide()
        
        self._cancel_button = ClientGUICommon.BetterBitmapButton( self, CC.GlobalBMPs.stop, self.Cancel )
        self._cancel_button.Bind( wx.EVT_RIGHT_DOWN, self.EventDismiss )
        self._cancel_button.Hide()
        
        hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        hbox.Add( self._pause_button, CC.FLAGS_VCENTER )
        hbox.Add( self._cancel_button, CC.FLAGS_VCENTER )
        
        yes_no_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        yes_no_hbox.Add( self._yes, CC.FLAGS_VCENTER )
        yes_no_hbox.Add( self._no, CC.FLAGS_VCENTER )
        
        vbox.Add( self._title, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._text_1, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._gauge_1, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._text_2, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._gauge_2, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._text_yes_no, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( yes_no_hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( self._network_job_ctrl, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._copy_to_clipboard_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._show_files_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._show_tb_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._tb_text, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._copy_tb_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( hbox, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
    
    def _NoButton( self ):
        
        self._job_key.SetVariable( 'popup_yes_no_answer', False )
        
        self._job_key.Delete()
        
        self._yes.Hide()
        self._no.Hide()
        
    
    def _ProcessText( self, text ):
        
        if len( text ) > self.TEXT_CUTOFF:
            
            new_text = 'The text is too long to display here. Here is the start of it (the rest is printed to the log):'
            
            new_text += os.linesep * 2
            
            new_text += text[:self.TEXT_CUTOFF]
            
            text = new_text
            
        
        return text
        
    
    def _YesButton( self ):
        
        self._job_key.SetVariable( 'popup_yes_no_answer', True )
        
        self._job_key.Delete()
        
        self._yes.Hide()
        self._no.Hide()
        
    
    def Cancel( self ):
        
        self._job_key.Cancel()
        
        self._pause_button.Disable()
        self._cancel_button.Disable()
        
    
    def CopyTB( self ):
        
        HG.client_controller.pub( 'clipboard', 'text', self._job_key.ToString() )
        
    
    def CopyToClipboard( self ):
        
        result = self._job_key.GetIfHasVariable( 'popup_clipboard' )
        
        if result is not None:
            
            ( title, text ) = result
            
            HG.client_controller.pub( 'clipboard', 'text', text )
            
        
    
    def PausePlay( self ):
        
        self._job_key.PausePlay()
        
        if self._job_key.IsPaused():
            
            ClientGUICommon.SetBitmapButtonBitmap( self._pause_button, CC.GlobalBMPs.play )
            
        else:
            
            ClientGUICommon.SetBitmapButtonBitmap( self._pause_button, CC.GlobalBMPs.pause )
            
        
    
    def ShowFiles( self ):
        
        result = self._job_key.GetIfHasVariable( 'popup_files' )
        
        if result is not None:
            
            ( popup_files, popup_files_name ) = result
            
            HG.client_controller.pub( 'new_page_query', CC.LOCAL_FILE_SERVICE_KEY, initial_hashes = popup_files, page_name = popup_files_name )
            
        
    
    def ShowTB( self ):
        
        if self._tb_text.IsShown():
            
            self._show_tb_button.SetLabelText( 'show traceback' )
            
            self._tb_text.Hide()
            
        else:
            
            self._show_tb_button.SetLabelText( 'hide traceback' )
            
            popup_message_character_width = HG.client_controller.new_options.GetInteger( 'popup_message_character_width' )
            
            wrap_width = ClientGUICommon.ConvertTextToPixelWidth( self._title, popup_message_character_width )
            
            self._tb_text.Show()
            
        
        self.GetParent().MakeSureEverythingFits()
        
    
    def GetJobKey( self ):
        
        return self._job_key
        
    
    def IsDeleted( self ):
        
        return self._job_key.IsDeleted()
        
    
    def TryToDismiss( self ):
        
        if self._job_key.IsPausable() or self._job_key.IsCancellable():
            
            return
            
        else:
            
            PopupWindow.TryToDismiss( self )
            
        
    
    def Update( self ):
        
        popup_message_character_width = HG.client_controller.new_options.GetInteger( 'popup_message_character_width' )
        
        wrap_width = ClientGUICommon.ConvertTextToPixelWidth( self._title, popup_message_character_width )
        
        paused = self._job_key.IsPaused()
        
        title = self._job_key.GetIfHasVariable( 'popup_title' )
        
        if title is not None:
            
            self._title.Show()
            
            self._title.SetLabelText( title )
            
        else:
            
            self._title.Hide()
            
        
        popup_text_1 = self._job_key.GetIfHasVariable( 'popup_text_1' )
        
        if popup_text_1 is not None or paused:
            
            if paused:
                
                text = 'paused'
                
            else:
                
                text = popup_text_1
                
            
            self._text_1.Show()
            
            self._text_1.SetLabelText( text )
            
        else:
            
            self._text_1.Hide()
            
        
        popup_gauge_1 = self._job_key.GetIfHasVariable( 'popup_gauge_1' )
        
        if popup_gauge_1 is not None and not paused:
            
            ( gauge_value, gauge_range ) = popup_gauge_1
            
            self._gauge_1.SetRange( gauge_range )
            self._gauge_1.SetValue( gauge_value )
            
            self._gauge_1.Show()
            
        else:
            
            self._gauge_1.Hide()
            
        
        popup_text_2 = self._job_key.GetIfHasVariable( 'popup_text_2' )
        
        if popup_text_2 is not None and not paused:
            
            text = popup_text_2
            
            self._text_2.SetLabelText( self._ProcessText( HydrusData.ToUnicode( text ) ) )
            
            self._text_2.Show()
            
        else:
            
            self._text_2.Hide()
            
        
        popup_gauge_2 = self._job_key.GetIfHasVariable( 'popup_gauge_2' )
        
        if popup_gauge_2 is not None and not paused:
            
            ( gauge_value, gauge_range ) = popup_gauge_2
            
            self._gauge_2.SetRange( gauge_range )
            self._gauge_2.SetValue( gauge_value )
            
            self._gauge_2.Show()
            
        else:
            
            self._gauge_2.Hide()
            
        
        popup_yes_no_question = self._job_key.GetIfHasVariable( 'popup_yes_no_question' )
        
        if popup_yes_no_question is not None and not paused:
            
            text = popup_yes_no_question
            
            if self._text_yes_no.GetLabelText() != text:
                
                self._text_yes_no.SetLabelText( self._ProcessText( HydrusData.ToUnicode( text ) ) )
                
            
            self._text_yes_no.Show()
            
            self._yes.Show()
            self._no.Show()
            
        else:
            
            self._text_yes_no.Hide()
            self._yes.Hide()
            self._no.Hide()
            
        
        popup_network_job = self._job_key.GetIfHasVariable( 'popup_network_job' )
        
        if popup_network_job is not None:
            
            self._network_job_ctrl.SetNetworkJob( popup_network_job )
            
            self._network_job_ctrl.Show()
            
        else:
            
            self._network_job_ctrl.ClearNetworkJob()
            
            self._network_job_ctrl.Hide()
            
        
        popup_clipboard = self._job_key.GetIfHasVariable( 'popup_clipboard' )
        
        if popup_clipboard is not None:
            
            ( title, text ) = popup_clipboard
            
            if self._copy_to_clipboard_button.GetLabelText() != title:
                
                self._copy_to_clipboard_button.SetLabelText( title )
                
            
            self._copy_to_clipboard_button.Show()
            
        else:
            
            self._copy_to_clipboard_button.Hide()
            
        
        result = self._job_key.GetIfHasVariable( 'popup_files' )
        
        if result is not None:
            
            ( popup_files, popup_files_name ) = result
            
            hashes = popup_files
            
            text = popup_files_name + ' - show ' + HydrusData.ToHumanInt( len( hashes ) ) + ' files'
            
            if self._show_files_button.GetLabelText() != text:
                
                self._show_files_button.SetLabelText( text )
                
            
            self._show_files_button.Show()
            
        else:
            
            self._show_files_button.Hide()
            
        
        popup_traceback = self._job_key.GetIfHasVariable( 'popup_traceback' )
        
        if popup_traceback is not None:
            
            self._copy_tb_button.Show()
            
        else:
            
            self._copy_tb_button.Hide()
            
        
        if popup_traceback is not None:
            
            text = popup_traceback
            
            if self._tb_text.GetLabelText() != text:
                
                self._tb_text.SetLabelText( self._ProcessText( HydrusData.ToUnicode( text ) ) )
                
            
            self._show_tb_button.Show()
            
        else:
            
            self._show_tb_button.Hide()
            self._tb_text.Hide()
            
        
        if self._job_key.IsPausable():
            
            self._pause_button.Show()
            
        else:
            
            self._pause_button.Hide()
            
        
        if self._job_key.IsCancellable():
            
            self._cancel_button.Show()
            
        else:
            
            self._cancel_button.Hide()
            
        
    
class PopupMessageManager( wx.Frame ):
    
    def __init__( self, parent ):
        
        wx.Frame.__init__( self, parent, style = wx.FRAME_TOOL_WINDOW | wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT | wx.BORDER_NONE )
        
        self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
        
        self._max_messages_to_display = 10
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        self._message_vbox = wx.BoxSizer( wx.VERTICAL )
        
        self._dismiss_all = PopupDismissAll( self )
        self._dismiss_all.Hide()
        
        vbox.Add( self._message_vbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( self._dismiss_all, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        self._pending_job_keys = []
        
        parent.Bind( wx.EVT_SIZE, self.EventMove )
        parent.Bind( wx.EVT_MOVE, self.EventMove )
        
        HG.client_controller.sub( self, 'AddMessage', 'message' )
        
        self._old_excepthook = sys.excepthook
        self._old_show_exception = HydrusData.ShowException
        
        sys.excepthook = ClientData.CatchExceptionClient
        HydrusData.ShowException = ClientData.ShowExceptionClient
        HydrusData.ShowText = ClientData.ShowTextClient
        
        job_key = ClientThreading.JobKey()
        
        job_key.SetVariable( 'popup_text_1', u'initialising popup message manager\u2026' )
        
        self._update_job = HG.client_controller.CallRepeatingWXSafe( self, 0.25, 0.5, self.REPEATINGUpdate )
        
        HG.client_controller.CallLaterWXSafe( self, 0.5, self.AddMessage, job_key )
        
        HG.client_controller.CallLaterWXSafe( self, 1.0, job_key.Delete )
        
    
    def _CheckPending( self ):
        
        force_relayout = False
        
        self._pending_job_keys = [ job_key for job_key in self._pending_job_keys if not job_key.IsDeleted() ]
        
        while len( self._pending_job_keys ) > 0 and self._message_vbox.GetItemCount() < self._max_messages_to_display:
            
            job_key = self._pending_job_keys.pop( 0 )
            
            window = PopupMessage( self, job_key )
            
            window.Update()
            
            self._message_vbox.Add( window, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            force_relayout = True
            
        
        dismiss_shown_before = self._dismiss_all.IsShown()
        
        num_messages_pending = len( self._pending_job_keys )
        
        if num_messages_pending > 0:
            
            self._dismiss_all.SetNumMessages( num_messages_pending )
            
            self._dismiss_all.Show()
            
        else:
            
            self._dismiss_all.Hide()
            
        
        if self._dismiss_all.IsShown() != dismiss_shown_before:
            
            force_relayout = True
            
        
        if force_relayout:
            
            self.Layout()
            
        
        if self._NeedsSizeOrShow():
            
            self._SizeAndPositionAndShow()
            
        
    
    def _DisplayingError( self ):
        
        sizer_items = self._message_vbox.GetChildren()
        
        for sizer_item in sizer_items:
            
            message_window = sizer_item.GetWindow()
            
            job_key = message_window.GetJobKey()
            
            if job_key.HasVariable( 'popup_traceback' ):
                
                return True
                
            
        
        return False
        
    
    def _DoDebugHide( self ):
        
        parent = self.GetParent()
        
        parent_iconized = parent.IsIconized()
        
        # changing show status while parent iconised in Windows leads to grey window syndrome
        windows_and_iconised = HC.PLATFORM_WINDOWS and parent_iconized
        
        possibly_on_hidden_virtual_desktop = not ClientGUITopLevelWindows.MouseIsOnMyDisplay( parent )
        
        going_to_bug_out_at_hide_or_show = windows_and_iconised or possibly_on_hidden_virtual_desktop
        
        new_options = HG.client_controller.new_options
        
        if new_options.GetBoolean( 'hide_message_manager_on_gui_iconise' ):
            
            if parent.IsIconized():
                
                self.Hide()
                
                return
                
            
        
        current_focus_tlp = wx.GetTopLevelParent( wx.Window.FindFocus() )
        
        main_gui_is_active = current_focus_tlp in ( self, parent )
        
        if new_options.GetBoolean( 'hide_message_manager_on_gui_deactive' ):
            
            if not main_gui_is_active:
                
                if not going_to_bug_out_at_hide_or_show:
                    
                    self.Hide()
                    
                
            
        
    
    def _NeedsSizeOrShow( self ):
        
        num_messages_displayed = self._message_vbox.GetItemCount()
        
        there_is_stuff_to_display = num_messages_displayed > 0
        
        is_shown = self.IsShown()
        
        if there_is_stuff_to_display:
            
            if not is_shown:
                
                return True
                
            
            best_size = self.GetBestSize()
            
            if best_size != self.GetSize():
                
                return True
                
            
        else:
            
            if is_shown:
                
                return True
                
            
        
        return False
        
    
    def _SizeAndPositionAndShow( self ):
        
        try:
            
            parent = self.GetParent()
            
            # changing show status while parent iconised in Windows leads to grey window syndrome
            windows_and_iconised = HC.PLATFORM_WINDOWS and parent.IsIconized()
            
            possibly_on_hidden_virtual_desktop = not ClientGUITopLevelWindows.MouseIsOnMyDisplay( parent )
            
            going_to_bug_out_at_hide_or_show = windows_and_iconised or possibly_on_hidden_virtual_desktop
            
            current_focus_tlp = wx.GetTopLevelParent( wx.Window.FindFocus() )
            
            main_gui_is_active = current_focus_tlp in ( self, parent )
            
            on_top_frame_is_active = False
            
            if not main_gui_is_active:
                
                c_f_tlp_is_child_frame_of_main_gui = isinstance( current_focus_tlp, wx.Frame ) and current_focus_tlp.GetParent() == parent
                
                if c_f_tlp_is_child_frame_of_main_gui and current_focus_tlp.GetWindowStyle() & wx.FRAME_FLOAT_ON_PARENT == wx.FRAME_FLOAT_ON_PARENT:
                    
                    on_top_frame_is_active = True
                    
                
            
            num_messages_displayed = self._message_vbox.GetItemCount()
            
            there_is_stuff_to_display = num_messages_displayed > 0
            
            if there_is_stuff_to_display:
                
                best_size = self.GetBestSize()
                
                if best_size != self.GetSize():
                    
                    self.Fit()
                    
                    self.Layout()
                    
                
                ( parent_width, parent_height ) = parent.GetClientSize()
                
                ( my_width, my_height ) = self.GetClientSize()
                
                my_x = ( parent_width - my_width ) - 25
                my_y = ( parent_height - my_height ) - 5
                
                if parent.IsShown():
                    
                    my_position = ClientGUICommon.ClientToScreen( parent, ( my_x, my_y ) )
                    
                    if my_position != self.GetPosition():
                        
                        self.SetPosition( my_position )
                        
                    
                
                # Unhiding tends to raise the main gui tlp, which is annoying if a media viewer window has focus
                show_is_not_annoying = main_gui_is_active or on_top_frame_is_active or self._DisplayingError()
                
                ok_to_show = show_is_not_annoying and not going_to_bug_out_at_hide_or_show
                
                if ok_to_show:
                    
                    was_hidden = not self.IsShown()
                    
                    self.Show()
                    
                    if was_hidden:
                        
                        self.Layout()
                        
                        self.Refresh()
                        
                    
                
            else:
                
                if not going_to_bug_out_at_hide_or_show:
                    
                    self.Hide()
                    
                
            
        except:
            
            text = 'The popup message manager experienced a fatal error and will now stop working! Please restart the client as soon as possible! If this keeps happening, please email the details and your client.log to the hydrus developer.'
            
            HydrusData.Print( text )
            
            HydrusData.Print( traceback.format_exc() )
            
            wx.MessageBox( text )
            
            self._update_job.Cancel()
            
            self.CleanBeforeDestroy()
            
            self.DestroyLater()
            
        
    
    def _GetAllMessageJobKeys( self ):
        
        job_keys = []
        
        sizer_items = self._message_vbox.GetChildren()
        
        for sizer_item in sizer_items:
            
            message_window = sizer_item.GetWindow()
            
            job_key = message_window.GetJobKey()
            
            job_keys.append( job_key )
            
        
        job_keys.extend( self._pending_job_keys )
        
        return job_keys
        
    
    def _OKToAlterUI( self ):
        
        main_gui = self.GetParent()
        
        not_on_hidden_or_virtual_display = ClientGUITopLevelWindows.MouseIsOnMyDisplay( main_gui )
        
        main_gui_up = not main_gui.IsIconized()
        
        return not_on_hidden_or_virtual_display and main_gui_up
        
    
    def _TryToMergeMessage( self, job_key ):
        
        if not job_key.HasVariable( 'popup_files_mergable' ):
            
            return False
            
        
        result = job_key.GetIfHasVariable( 'popup_files' )
        
        if result is not None:
            
            ( hashes, name ) = result
            
            existing_job_keys = self._GetAllMessageJobKeys()
            
            for existing_job_key in existing_job_keys:
                
                if existing_job_key.HasVariable( 'popup_files_mergable' ):
                    
                    result = existing_job_key.GetIfHasVariable( 'popup_files' )
                    
                    if result is not None:
                        
                        ( existing_hashes, existing_name ) = result
                        
                        if existing_name == name:
                            
                            if isinstance( existing_hashes, list ):
                                
                                existing_hashes.extend( hashes )
                                
                            elif isinstance( existing_hashes, set ):
                                
                                existing_hashes.update( hashes )
                                
                            
                            return True
                            
                        
                    
                
            
        
        return False
        
    
    def _Update( self ):
        
        if HG.view_shutdown:
            
            self._update_job.Cancel()
            
            self.CleanBeforeDestroy()
            
            self.DestroyLater()
            
            return
            
        
        sizer_items = self._message_vbox.GetChildren()
        
        for sizer_item in sizer_items:
            
            message_window = sizer_item.GetWindow()
            
            if message_window.IsDeleted():
                
                message_window.TryToDismiss()
                
                self.Layout()
                
                break
                
            else:
                
                message_window.Update()
                
            
        
    
    def AddMessage( self, job_key ):
        
        try:
            
            was_merged = self._TryToMergeMessage( job_key )
            
            if was_merged:
                
                return
                
            
            self._pending_job_keys.append( job_key )
            
            if self._OKToAlterUI():
                
                self._CheckPending()
                
            
        except:
            
            HydrusData.Print( traceback.format_exc() )
            
        
    
    def CleanBeforeDestroy( self ):
        
        for job_key in self._pending_job_keys:
            
            if job_key.IsCancellable():
                
                job_key.Cancel()
                
            
        
        sizer_items = self._message_vbox.GetChildren()
        
        for sizer_item in sizer_items:
            
            message_window = sizer_item.GetWindow()
            
            job_key = message_window.GetJobKey()
            
            if job_key.IsCancellable():
                
                job_key.Cancel()
                
            
        
        sys.excepthook = self._old_excepthook
        
        HydrusData.ShowException = self._old_show_exception
        
    
    def Dismiss( self, window ):
        
        self._message_vbox.Detach( window )
        
        window.DestroyLater()
        
        if self._OKToAlterUI():
            
            self.Layout()
            
            self._CheckPending()
            
        
    
    def DismissAll( self ):
        
        self._pending_job_keys = [ job_key for job_key in self._pending_job_keys if job_key.IsPausable() or job_key.IsCancellable() ]
        
        sizer_items = self._message_vbox.GetChildren()
        
        for sizer_item in sizer_items:
            
            message_window = sizer_item.GetWindow()
            
            message_window.TryToDismiss()
            
        
        self.Layout()
        
        self._CheckPending()
        
    
    def EventMove( self, event ):
        
        if self._OKToAlterUI():
            
            self._SizeAndPositionAndShow()
            
        
        event.Skip()
        
    
    def MakeSureEverythingFits( self ):
        
        if self._OKToAlterUI():
            
            self.Layout()
            
            self._SizeAndPositionAndShow()
            
        
    
    def REPEATINGUpdate( self ):
        
        try:
            
            self._DoDebugHide()
            
            if self._OKToAlterUI():
                
                self._Update()
                
                self._CheckPending()
                
            
        except:
            
            self._update_job.Cancel()
            
            raise
            
        
    
class PopupMessageDialogPanel( ClientGUIScrolledPanels.ReviewPanelVetoable ):
    
    def __init__( self, parent, job_key ):
        
        ClientGUIScrolledPanels.ReviewPanelVetoable.__init__( self, parent )
        
        self._job_key = job_key
        
        self._message_window = PopupMessage( self, self._job_key )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._message_window, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self._windows_hidden = []
        
        self._HideOtherWindows()
        
        self._message_pubbed = False
        
        self._update_job = HG.client_controller.CallRepeatingWXSafe( self, 0.25, 0.5, self.REPEATINGUpdate )
        
    
    def _HideOtherWindows( self ):
        
        for tlw in wx.GetTopLevelWindows():
            
            if tlw == self:
                
                continue
                
            
            if not isinstance( tlw, ( ClientGUITopLevelWindows.Frame, ClientGUITopLevelWindows.NewDialog ) ):
                
                continue
                
            
            import ClientGUI
            
            if isinstance( tlw, ClientGUI.FrameGUI ):
                
                continue
                
            
            if not tlw.IsShown() or tlw.IsIconized():
                
                continue
                
            
            tlw.Hide()
            
            self._windows_hidden.append( tlw )
            
        
    
    def _ReleaseMessage( self ):
        
        if not self._message_pubbed:
            
            HG.client_controller.pub( 'message', self._job_key )
            
            self._message_pubbed = True
            
            self._RestoreOtherWindows()
            
        
    
    def _RestoreOtherWindows( self ):
        
        for tlw in self._windows_hidden:
            
            tlw.Show()
            
        
        self._windows_hidden = []
        
    
    def _Update( self ):
        
        self._message_window.Update()
        
        best_size = self.GetBestSize()
        
        if best_size != self.GetSize():
            
            ClientGUITopLevelWindows.PostSizeChangedEvent( self )
            
        
    
    def Dismiss( self, window ):
        
        return
        
    
    def TryToClose( self ):
        
        if self._job_key.IsDone():
            
            self._ReleaseMessage()
            
        else:
            
            if self._job_key.IsCancellable():
                
                with ClientGUIDialogs.DialogYesNo( self, 'Cancel/stop job?' ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_YES:
                        
                        self._job_key.Cancel()
                        
                        self._ReleaseMessage()
                        
                    else:
                        
                        raise HydrusExceptions.VetoException()
                        
                    
                
            else:
                
                raise HydrusExceptions.VetoException( 'Unfortunately, this job cannot be cancelled. If it really is taking too long, please kill the client through task manager.' )
                
            
        
    
    def REPEATINGUpdate( self ):
        
        try:
            
            if self._job_key.IsDone():
                
                parent = self.GetParent()
                
                if parent.IsModal(): # event sometimes fires after modal done
                    
                    self.GetParent().DoOK()
                    
                
            else:
                
                self._Update()
                
            
        except:
            
            self._update_job.Cancel()
            
            raise
            
        
    
