import ClientCaches
import ClientConstants as CC
import ClientData
import ClientDefaults
import ClientDownloading
import ClientDragDrop
import ClientExporting
import ClientFiles
import ClientGUIACDropdown
import ClientGUICommon
import ClientGUIListBoxes
import ClientGUIListCtrl
import ClientGUIDialogs
import ClientGUIImport
import ClientGUIOptionsPanels
import ClientGUIPredicates
import ClientGUIScrolledPanelsEdit
import ClientGUIShortcuts
import ClientGUIFileSeedCache
import ClientGUITime
import ClientGUITopLevelWindows
import ClientImporting
import ClientImportOptions
import ClientMedia
import ClientRatings
import ClientSearch
import ClientServices
import ClientThreading
import collections
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals as HG
import HydrusNATPunch
import HydrusNetwork
import HydrusPaths
import HydrusSerialisable
import HydrusTagArchive
import HydrusTags
import HydrusText
import itertools
import multipart
import os
import random
import re
import string
import time
import traceback
import wx
import yaml

# Option Enums

ID_NULL = wx.NewId()

ID_TIMER_UPDATE = wx.NewId()

def GenerateMultipartFormDataCTAndBodyFromDict( fields ):
    
    m = multipart.Multipart()
    
    for ( name, value ) in fields.items(): m.field( name, HydrusData.ToByteString( value ) )
    
    return m.get()
    
class DialogManageBoorus( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage boorus' )
        
        self._names_to_delete = []
        
        self._boorus = ClientGUICommon.ListBook( self )
        
        self._add = wx.Button( self, label = 'add' )
        self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
        self._add.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._remove = wx.Button( self, label = 'remove' )
        self._remove.Bind( wx.EVT_BUTTON, self.EventRemove )
        self._remove.SetForegroundColour( ( 128, 0, 0 ) )
        
        menu_items = []
        
        menu_items.append( ( 'normal', 'all', 'restore all defaults', self._RestoreDefault ) )
        menu_items.append( ( 'separator', 0, 0, 0 ) )
        
        default_booru_data = list( ClientDefaults.GetDefaultBoorus().items() )
        
        default_booru_data.sort()
        
        for ( name, booru ) in default_booru_data:
            
            menu_items.append( ( 'normal', name, 'add this booru from the defaults', HydrusData.Call( self._RestoreDefault, booru ) ) )
            
        
        self._restore_default = ClientGUICommon.MenuButton( self, 'restore default', menu_items )
        
        self._export = wx.Button( self, label = 'export' )
        self._export.Bind( wx.EVT_BUTTON, self.EventExport )
        
        self._ok = wx.Button( self, id = wx.ID_OK,  label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        boorus = HG.client_controller.Read( 'remote_boorus' )
        
        for ( name, booru ) in boorus.items():
            
            self._boorus.AddPageArgs( name, name, self._Panel, ( self._boorus, booru ), {} )
            
        
        #
        
        add_remove_hbox = wx.BoxSizer( wx.HORIZONTAL )
        add_remove_hbox.Add( self._add, CC.FLAGS_VCENTER )
        add_remove_hbox.Add( self._remove, CC.FLAGS_VCENTER )
        add_remove_hbox.Add( self._restore_default, CC.FLAGS_VCENTER )
        add_remove_hbox.Add( self._export, CC.FLAGS_VCENTER )
        
        ok_hbox = wx.BoxSizer( wx.HORIZONTAL )
        ok_hbox.Add( self._ok, CC.FLAGS_VCENTER )
        ok_hbox.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        vbox.Add( self._boorus, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( add_remove_hbox, CC.FLAGS_SMALL_INDENT )
        vbox.Add( ok_hbox, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        self.SetDropTarget( ClientDragDrop.FileDropTarget( self, filenames_callable = self.Import ) )
    
        ( x, y ) = self.GetEffectiveMinSize()
        
        self.SetInitialSize( ( 980, y ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def _RestoreDefault( self, booru = None ):
        
        if booru is None:
            
            for booru in ClientDefaults.GetDefaultBoorus().values():
                
                self._RestoreDefault( booru )
                
            
        else:
            
            name = booru.GetName()
            
            if self._boorus.KeyExists( name ):
                
                message = '\'' + name + '\' already exists--are you sure you want to overwrite it with the default entry?'
                
                with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_YES:
                        
                        self._boorus.Select( name )
                        
                        page = self._boorus.GetPage( name )
                        
                        page.Update( booru )
                        
                    
                
            else:
                
                page = self._Panel( self._boorus, booru, is_new = True )
                
                self._boorus.AddPage( name, name, page, select = True )
                
            
        
    
    def EventAdd( self, event ):
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter new booru\'s name.' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                try:
                    
                    name = dlg.GetValue()
                    
                    if self._boorus.KeyExists( name ):
                        
                        raise HydrusExceptions.NameException( 'That name is already in use!' )
                        
                    
                    if name == '':
                        
                        raise HydrusExceptions.NameException( 'Please enter a nickname for the booru.' )
                        
                    
                    booru = ClientData.Booru( name, 'search_url', '+', 1, 'thumbnail', '', 'original image', {} )
                    
                    page = self._Panel( self._boorus, booru, is_new = True )
                    
                    self._boorus.AddPage( name, name, page, select = True )
                    
                except HydrusExceptions.NameException as e:
                    
                    wx.MessageBox( HydrusData.ToUnicode( e ) )
                    
                    self.EventAdd( event )
                    
                
            
        
    
    def EventExport( self, event ):
        
        booru_panel = self._boorus.GetCurrentPage()
        
        if booru_panel is not None:
            
            name = self._boorus.GetCurrentKey()
            
            booru = booru_panel.GetBooru()
            
            with wx.FileDialog( self, 'select where to export booru', defaultFile = 'booru.yaml', style = wx.FD_SAVE ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    path = HydrusData.ToUnicode( dlg.GetPath() )
                    
                    with open( path, 'wb' ) as f: f.write( yaml.safe_dump( booru ) )
                    
                
            
        
    
    def EventOK( self, event ):
        
        try:
            
            for name in self._names_to_delete:
                
                HG.client_controller.Write( 'delete_remote_booru', name )
                
            
            for page in self._boorus.GetActivePages():
                
                if page.HasChanges():
                    
                    booru = page.GetBooru()
                    
                    name = booru.GetName()
                    
                    HG.client_controller.Write( 'remote_booru', name, booru )
                    
                
            
        finally: self.EndModal( wx.ID_OK )
        
    
    def EventRemove( self, event ):
        
        booru_panel = self._boorus.GetCurrentPage()
        
        if booru_panel is not None:
            
            name = self._boorus.GetCurrentKey()
            
            self._names_to_delete.append( name )
            
            self._boorus.DeleteCurrentPage()
            
        
    
    def Import( self, paths ):
        
        for path in paths:
            
            try:
                
                with open( path, 'rb' ) as f: file = f.read()
                
                thing = yaml.safe_load( file )
                
                if isinstance( thing, ClientData.Booru ):
                    
                    booru = thing
                    
                    name = booru.GetName()
                    
                    if not self._boorus.KeyExists( name ):
                        
                        new_booru = ClientData.Booru( name, 'search_url', '+', 1, 'thumbnail', '', 'original image', {} )
                        
                        page = self._Panel( self._boorus, new_booru, is_new = True )
                        
                        self._boorus.AddPage( name, name, page, select = True )
                        
                    
                    self._boorus.Select( name )
                    
                    page = self._boorus.GetPage( name )
                    
                    page.Update( booru )
                    
                
            except:
                
                wx.MessageBox( traceback.format_exc() )
                
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, booru, is_new = False ):
            
            wx.Panel.__init__( self, parent )
            
            self._booru = booru
            self._is_new = is_new
            
            ( search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces ) = booru.GetData()
            
            self._booru_panel = ClientGUICommon.StaticBox( self, 'booru' )
            
            #
            
            self._search_panel = ClientGUICommon.StaticBox( self._booru_panel, 'search' )
            
            self._search_url = wx.TextCtrl( self._search_panel )
            self._search_url.Bind( wx.EVT_TEXT, self.EventHTML )
            
            self._search_separator = wx.Choice( self._search_panel, choices = [ '+', '&', '%20' ] )
            self._search_separator.Bind( wx.EVT_CHOICE, self.EventHTML )
            
            self._advance_by_page_num = wx.CheckBox( self._search_panel )
            
            self._thumb_classname = wx.TextCtrl( self._search_panel )
            self._thumb_classname.Bind( wx.EVT_TEXT, self.EventHTML )
            
            self._example_html_search = wx.StaticText( self._search_panel, style = wx.ST_NO_AUTORESIZE )
            
            #
            
            self._image_panel = ClientGUICommon.StaticBox( self._booru_panel, 'image' )
            
            self._image_info = wx.TextCtrl( self._image_panel )
            self._image_info.Bind( wx.EVT_TEXT, self.EventHTML )
            
            self._image_id = wx.RadioButton( self._image_panel, style = wx.RB_GROUP )
            self._image_id.Bind( wx.EVT_RADIOBUTTON, self.EventHTML )
            
            self._image_data = wx.RadioButton( self._image_panel )
            self._image_data.Bind( wx.EVT_RADIOBUTTON, self.EventHTML )
            
            self._example_html_image = wx.StaticText( self._image_panel, style = wx.ST_NO_AUTORESIZE )
            
            #
            
            self._tag_panel = ClientGUICommon.StaticBox( self._booru_panel, 'tags' )
            
            self._tag_classnames_to_namespaces = wx.ListBox( self._tag_panel )
            self._tag_classnames_to_namespaces.Bind( wx.EVT_LEFT_DCLICK, self.EventRemove )
            
            self._tag_classname = wx.TextCtrl( self._tag_panel )
            self._namespace = wx.TextCtrl( self._tag_panel )
            
            self._add = wx.Button( self._tag_panel, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
            
            self._example_html_tags = wx.StaticText( self._tag_panel, style = wx.ST_NO_AUTORESIZE )
            
            #
            
            self._search_url.SetValue( search_url )
            
            self._search_separator.Select( self._search_separator.FindString( search_separator ) )
            
            self._advance_by_page_num.SetValue( advance_by_page_num )
            
            self._thumb_classname.SetValue( thumb_classname )
            
            #
            
            if image_id is None:
                
                self._image_info.SetValue( image_data )
                self._image_data.SetValue( True )
                
            else:
                
                self._image_info.SetValue( image_id )
                self._image_id.SetValue( True )
                
            
            #
            
            for ( tag_classname, namespace ) in tag_classnames_to_namespaces.items(): self._tag_classnames_to_namespaces.Append( tag_classname + ' : ' + namespace, ( tag_classname, namespace ) )
            
            #
            
            rows = []
            
            rows.append( ( 'search url: ', self._search_url ) )
            rows.append( ( 'search tag separator: ', self._search_separator ) )
            rows.append( ( 'advance by page num: ', self._advance_by_page_num ) )
            rows.append( ( 'thumbnail classname: ', self._thumb_classname ) )
            
            gridbox = ClientGUICommon.WrapInGrid( self._search_panel, rows )
            
            self._search_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            self._search_panel.Add( self._example_html_search, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            rows = []
            
            rows.append( ( 'text: ', self._image_info ) )
            rows.append( ( 'id of <img>: ', self._image_id ) )
            rows.append( ( 'text of <a>: ', self._image_data ) )
            
            gridbox = ClientGUICommon.WrapInGrid( self._image_panel, rows )
            
            self._image_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            self._image_panel.Add( self._example_html_image, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.Add( self._tag_classname, CC.FLAGS_VCENTER )
            hbox.Add( self._namespace, CC.FLAGS_VCENTER )
            hbox.Add( self._add, CC.FLAGS_VCENTER )
            
            self._tag_panel.Add( self._tag_classnames_to_namespaces, CC.FLAGS_EXPAND_BOTH_WAYS )
            self._tag_panel.Add( hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            self._tag_panel.Add( self._example_html_tags, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            #
            
            self._booru_panel.Add( self._search_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            self._booru_panel.Add( self._image_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            self._booru_panel.Add( self._tag_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._booru_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            self.SetSizer( vbox )
            
        
        def _GetInfo( self ):
            
            booru_name = self._booru.GetName()
            
            search_url = self._search_url.GetValue()
            
            search_separator = self._search_separator.GetStringSelection()
            
            advance_by_page_num = self._advance_by_page_num.GetValue()
            
            thumb_classname = self._thumb_classname.GetValue()
            
            if self._image_id.GetValue():
                
                image_id = self._image_info.GetValue()
                image_data = None
                
            else:
                
                image_id = None
                image_data = self._image_info.GetValue()
                
            
            tag_classnames_to_namespaces = { tag_classname : namespace for ( tag_classname, namespace ) in [ self._tag_classnames_to_namespaces.GetClientData( i ) for i in range( self._tag_classnames_to_namespaces.GetCount() ) ] }
            
            return ( booru_name, search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces )
            
        
        def EventAdd( self, event ):
            
            tag_classname = self._tag_classname.GetValue()
            namespace = self._namespace.GetValue()
            
            if tag_classname != '':
                
                self._tag_classnames_to_namespaces.Append( tag_classname + ' : ' + namespace, ( tag_classname, namespace ) )
                
                self._tag_classname.SetValue( '' )
                self._namespace.SetValue( '' )
                
                self.EventHTML( event )
                
            
        
        def EventHTML( self, event ):
            
            pass
            
        
        def EventRemove( self, event ):
            
            selection = self._tag_classnames_to_namespaces.GetSelection()
            
            if selection != wx.NOT_FOUND:
                
                self._tag_classnames_to_namespaces.Delete( selection )
                
                self.EventHTML( event )
                
            
        
        def GetBooru( self ):
            
            ( booru_name, search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces ) = self._GetInfo()
            
            return ClientData.Booru( booru_name, search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces )
            
        
        def HasChanges( self ):
            
            if self._is_new: return True
            
            ( booru_name, my_search_url, my_search_separator, my_advance_by_page_num, my_thumb_classname, my_image_id, my_image_data, my_tag_classnames_to_namespaces ) = self._GetInfo()
            
            ( search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces ) = self._booru.GetData()
            
            if search_url != my_search_url: return True
            
            if search_separator != my_search_separator: return True
            
            if advance_by_page_num != my_advance_by_page_num: return True
            
            if thumb_classname != my_thumb_classname: return True
            
            if image_id != my_image_id: return True
            
            if image_data != my_image_data: return True
            
            if tag_classnames_to_namespaces != my_tag_classnames_to_namespaces: return True
            
            return False
            
        
        def Update( self, booru ):
            
            ( search_url, search_separator, advance_by_page_num, thumb_classname, image_id, image_data, tag_classnames_to_namespaces ) = booru.GetData()
            
            self._search_url.SetValue( search_url )
            
            self._search_separator.Select( self._search_separator.FindString( search_separator ) )
            
            self._advance_by_page_num.SetValue( advance_by_page_num )
            
            self._thumb_classname.SetValue( thumb_classname )
            
            if image_id is None:
                
                self._image_info.SetValue( image_data )
                self._image_data.SetValue( True )
                
            else:
                
                self._image_info.SetValue( image_id )
                self._image_id.SetValue( True )
                
            
            self._tag_classnames_to_namespaces.Clear()
            
            for ( tag_classname, namespace ) in tag_classnames_to_namespaces.items(): self._tag_classnames_to_namespaces.Append( tag_classname + ' : ' + namespace, ( tag_classname, namespace ) )
            
        
    '''
class DialogManageContacts( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        def InitialiseControls():
            
            self._contacts = ClientGUICommon.ListBook( self )
            
            self._contacts.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGING, self.EventContactChanging )
            self._contacts.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventContactChanged )
            
            self._add_contact_address = wx.Button( self, label = 'add by contact address' )
            self._add_contact_address.Bind( wx.EVT_BUTTON, self.EventAddByContactAddress )
            self._add_contact_address.SetForegroundColour( ( 0, 128, 0 ) )
            
            self._add_manually = wx.Button( self, label = 'add manually' )
            self._add_manually.Bind( wx.EVT_BUTTON, self.EventAddManually )
            self._add_manually.SetForegroundColour( ( 0, 128, 0 ) )
            
            self._remove = wx.Button( self, label = 'remove' )
            self._remove.Bind( wx.EVT_BUTTON, self.EventRemove )
            self._remove.SetForegroundColour( ( 128, 0, 0 ) )
            
            self._export = wx.Button( self, label = 'export' )
            self._export.Bind( wx.EVT_BUTTON, self.EventExport )
            
            self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
            self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
            self._ok.SetForegroundColour( ( 0, 128, 0 ) )
            
            self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
            self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
            
        
        def PopulateControls():
            
            self._edit_log = []
            
            ( identities, contacts, deletable_names ) = HG.client_controller.Read( 'identities_and_contacts' )
            
            self._deletable_names = deletable_names
            
            for identity in identities:
                
                name = identity.GetName()
                
                page_info = ( self._Panel, ( self._contacts, identity ), { 'is_identity' : True } )
                
                self._contacts.AddPage( page_info, ' identity - ' + name )
                
            
            for contact in contacts:
                
                name = contact.GetName()
                
                page_info = ( self._Panel, ( self._contacts, contact ), { 'is_identity' : False } )
                
                self._contacts.AddPage( page_info, name )
                
            
        
        def ArrangeControls():
            
            add_remove_hbox = wx.BoxSizer( wx.HORIZONTAL )
            add_remove_hbox.Add( self._add_manually, CC.FLAGS_VCENTER )
            add_remove_hbox.Add( self._add_contact_address, CC.FLAGS_VCENTER )
            add_remove_hbox.Add( self._remove, CC.FLAGS_VCENTER )
            add_remove_hbox.Add( self._export, CC.FLAGS_VCENTER )
            
            ok_hbox = wx.BoxSizer( wx.HORIZONTAL )
            ok_hbox.Add( self._ok, CC.FLAGS_VCENTER )
            ok_hbox.Add( self._cancel, CC.FLAGS_VCENTER )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            vbox.Add( self._contacts, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.Add( add_remove_hbox, CC.FLAGS_SMALL_INDENT )
            vbox.Add( ok_hbox, CC.FLAGS_BUTTON_SIZER )
            
            self.SetSizer( vbox )
            
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage contacts' )
        
        InitialiseControls()
        
        PopulateControls()
        
        ArrangeControls()
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        self.SetInitialSize( ( 980, y ) )
        
        self.SetDropTarget( ClientDragDrop.FileDropTarget( filenames_callable = self.Import ) )
        
        self.EventContactChanged( None )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def _CheckCurrentContactIsValid( self ):
        
        contact_panel = self._contacts.GetCurrentPage()
        
        if contact_panel is not None:
            
            contact = contact_panel.GetContact()
            
            old_name = self._contacts.GetCurrentName()
            name = contact.GetName()
            
            if name != old_name and ' identity - ' + name != old_name:
                
                if self._contacts.NameExists( name ) or self._contacts.NameExists( ' identity - ' + name ) or name == 'Anonymous': raise Exception( 'That name is already in use!' )
                
                if old_name.startswith( ' identity - ' ): self._contacts.RenamePage( old_name, ' identity - ' + name )
                else: self._contacts.RenamePage( old_name, name )
                
            
        
    
    def EventAddByContactAddress( self, event ):
        
        try: self._CheckCurrentContactIsValid()
        except Exception as e:
            
            wx.MessageBox( HydrusData.ToUnicode( e ) )
            
            return
            
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter contact\'s address in the form contact_key@hostname:port.' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                contact_address = dlg.GetValue()
                
                try:
                    
                    ( contact_key_encoded, address ) = contact_address.split( '@' )
                    
                    contact_key = contact_key_encoded.decode( 'hex' )
                    
                    ( host, port ) = address.split( ':' )
                    
                    port = int( port )
                    
                except: raise Exception( 'Could not parse the address!' )
                
                name = contact_key_encoded
                
                contact = ClientConstantsMessages.Contact( None, name, host, port )
                
                try:
                    
                    connection = contact.GetConnection()
                    
                    public_key = connection.Get( 'public_key', contact_key = contact_key.encode( 'hex' ) )
                    
                except: raise Exception( 'Could not fetch the contact\'s public key from the address:' + os.linesep + traceback.format_exc() )
                
                contact = ClientConstantsMessages.Contact( public_key, name, host, port )
                
                self._edit_log.append( ( HC.ADD, contact ) )
                
                page = self._Panel( self._contacts, contact, is_identity = False )
                
                self._deletable_names.add( name )
                
                self._contacts.AddPage( page, name, select = True )
                
            
        
    
    def EventAddManually( self, event ):
        
        try: self._CheckCurrentContactIsValid()
        except Exception as e:
            
            wx.MessageBox( HydrusData.ToUnicode( e ) )
            
            return
            
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter new contact\'s name.' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                name = dlg.GetValue()
                
                if self._contacts.NameExists( name ) or self._contacts.NameExists( ' identity - ' + name ) or name == 'Anonymous': raise Exception( 'That name is already in use!' )
                
                if name == '': raise Exception( 'Please enter a nickname for the service.' )
                
                public_key = None
                host = 'hostname'
                port = 45871
                
                contact = ClientConstantsMessages.Contact( public_key, name, host, port )
                
                self._edit_log.append( ( HC.ADD, contact ) )
                
                page = self._Panel( self._contacts, contact, is_identity = False )
                
                self._deletable_names.add( name )
                
                self._contacts.AddPage( page, name, select = True )
                
            
        
    
    def EventContactChanged( self, event ):
        
        contact_panel = self._contacts.GetCurrentPage()
        
        if contact_panel is not None:
            
            old_name = contact_panel.GetOriginalName()
            
            if old_name in self._deletable_names: self._remove.Enable()
            else: self._remove.Disable()
            
        
    
    def EventContactChanging( self, event ):
        
        try: self._CheckCurrentContactIsValid()
        except Exception as e:
            
            wx.MessageBox( HydrusData.ToUnicode( e ) )
            
            event.Veto()
            
        
    
    def EventExport( self, event ):
        
        contact_panel = self._contacts.GetCurrentPage()
        
        if contact_panel is not None:
            
            name = self._contacts.GetCurrentName()
            
            contact = contact_panel.GetContact()
            
            try:
                
                with wx.FileDialog( self, 'select where to export contact', defaultFile = name + '.yaml', style = wx.FD_SAVE ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        path = HydrusData.ToUnicode( dlg.GetPath() )
                        
                        with open( path, 'wb' ) as f: f.write( yaml.safe_dump( contact ) )
                        
                    
                
            except:
                
                with wx.FileDialog( self, 'select where to export contact', defaultFile = 'contact.yaml', style = wx.FD_SAVE ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        path = HydrusData.ToUnicode( dlg.GetPath() )
                        
                        with open( path, 'wb' ) as f: f.write( yaml.safe_dump( contact ) )
                        
                    
                
            
        
    
    def EventOK( self, event ):
        
        try: self._CheckCurrentContactIsValid()
        except Exception as e:
            
            wx.MessageBox( HydrusData.ToUnicode( e ) )
            
            return
            
        
        for ( name, page ) in self._contacts.GetNamesToActivePages().items():
            
            if page.HasChanges(): self._edit_log.append( ( HC.EDIT, ( page.GetOriginalName(), page.GetContact() ) ) )
            
        
        try:
            
            if len( self._edit_log ) > 0: HG.client_controller.Write( 'update_contacts', self._edit_log )
            
        finally: self.EndModal( wx.ID_OK )
        
    
    # this isn't used yet!
    def EventRemove( self, event ):
        
        contact_panel = self._contacts.GetCurrentPage()
        
        if contact_panel is not None:
            
            name = contact_panel.GetOriginalName()
            
            self._edit_log.append( ( HC.DELETE, name ) )
            
            self._contacts.DeleteCurrentPage()
            
            self._deletable_names.discard( name )
            
        
    
    def Import( self, paths ):
        
        try: self._CheckCurrentContactIsValid()
        except Exception as e:
            
            wx.MessageBox( HydrusData.ToUnicode( e ) )
            
            return
            
        
        for path in paths:
            
            try:
                
                with open( path, 'rb' ) as f: file = f.read()
                
                obj = yaml.safe_load( file )
                
                if type( obj ) == ClientConstantsMessages.Contact:
                    
                    contact = obj
                    
                    name = contact.GetName()
                    
                    if self._contacts.NameExists( name ) or self._contacts.NameExists( ' identities - ' + name ) or name == 'Anonymous':
                        
                        message = 'There already exists a contact or identity with the name ' + name + '. Do you want to overwrite, or make a new contact?'
                        
                        with ClientGUIDialogs.DialogYesNo( self, message, title = 'Please choose what to do.', yes_label = 'overwrite', no_label = 'make new' ) as dlg:
                            
                            if True:
                                
                                name_to_page_dict = self._contacts.GetNamesToActivePages()
                                
                                if name in name_to_page_dict: page = name_to_page_dict[ name ]
                                else: page = name_to_page_dict[ ' identities - ' + name ]
                                
                                page.Update( contact )
                                
                            else:
                                
                                while self._contacts.NameExists( name ) or self._contacts.NameExists( ' identities - ' + name ) or name == 'Anonymous': name = name + str( random.randint( 0, 9 ) )
                                
                                ( public_key, old_name, host, port ) = contact.GetInfo()
                                
                                new_contact = ClientConstantsMessages.Contact( public_key, name, host, port )
                                
                                self._edit_log.append( ( HC.ADD, contact ) )
                                
                                self._deletable_names.add( name )
                                
                                page = self._Panel( self._contacts, contact, False )
                                
                                self._contacts.AddPage( page, name, select = True )
                                
                            
                        
                    else:
                        
                        ( public_key, old_name, host, port ) = contact.GetInfo()
                        
                        new_contact = ClientConstantsMessages.Contact( public_key, name, host, port )
                        
                        self._edit_log.append( ( HC.ADD, contact ) )
                        
                        self._deletable_names.add( name )
                        
                        page = self._Panel( self._contacts, contact, False )
                        
                        self._contacts.AddPage( page, name, select = True )
                        
                    
                
            except:
                
                wx.MessageBox( traceback.format_exc() )
                
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, contact, is_identity ):
            
            wx.Panel.__init__( self, parent )
            
            self._contact = contact
            self._is_identity = is_identity
            
            ( public_key, name, host, port ) = contact.GetInfo()
            
            contact_key = contact.GetContactKey()
            
            def InitialiseControls():
                
                self._contact_panel = ClientGUICommon.StaticBox( self, 'contact' )
                
                self._name = wx.TextCtrl( self._contact_panel )
                
                self._contact_address = wx.TextCtrl( self._contact_panel )
                
                self._public_key = ClientGUICommon.SaneMultilineTextCtrl( self._contact_panel )
                
            
            def PopulateControls():
                
                self._name.SetValue( name )
                
                contact_address = host + ':' + str( port )
                
                if contact_key is not None: contact_address = contact_key.encode( 'hex' ) + '@' + contact_address
                
                self._contact_address.SetValue( contact_address )
                
                if public_key is not None: self._public_key.SetValue( public_key )
                
            
            def ArrangeControls():
                
                gridbox = wx.FlexGridSizer( 2 )
                
                gridbox.AddGrowableCol( 1, 1 )
                
                gridbox.Add( wx.StaticText( self._contact_panel, label = 'name' ), CC.FLAGS_VCENTER )
                gridbox.Add( self._name, CC.FLAGS_EXPAND_BOTH_WAYS )
                gridbox.Add( wx.StaticText( self._contact_panel, label = 'contact address' ), CC.FLAGS_VCENTER )
                gridbox.Add( self._contact_address, CC.FLAGS_EXPAND_BOTH_WAYS )
                gridbox.Add( wx.StaticText( self._contact_panel, label = 'public key' ), CC.FLAGS_VCENTER )
                gridbox.Add( self._public_key, CC.FLAGS_EXPAND_BOTH_WAYS )
                
                self._contact_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
                
                vbox = wx.BoxSizer( wx.VERTICAL )
                
                vbox.Add( self._contact_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                
                self.SetSizer( vbox )
                
            
            InitialiseControls()
            
            PopulateControls()
            
            ArrangeControls()
            
        
        def _GetInfo( self ):
            
            public_key = self._public_key.GetValue()
            
            if public_key == '': public_key = None
            
            name = self._name.GetValue()
            
            contact_address = self._contact_address.GetValue()
            
            try:
                
                if '@' in contact_address: ( contact_key, address ) = contact_address.split( '@' )
                else: address = contact_address
                
                ( host, port ) = address.split( ':' )
                
                try: port = int( port )
                except:
                    
                    port = 45871
                    
                    wx.MessageBox( 'Could not parse the port!' )
                    
                
            except:
                
                host = 'hostname'
                port = 45871
                
                wx.MessageBox( 'Could not parse the contact\'s address!' )
                
            
            return [ public_key, name, host, port ]
            
        
        def GetContact( self ):
            
            [ public_key, name, host, port ] = self._GetInfo()
            
            return ClientConstantsMessages.Contact( public_key, name, host, port )
            
        
        def GetOriginalName( self ): return self._contact.GetName()
        
        def HasChanges( self ):
            
            [ my_public_key, my_name, my_host, my_port ] = self._GetInfo()
            
            [ public_key, name, host, port ] = self._contact.GetInfo()
            
            if my_public_key != public_key: return True
            
            if my_name != name: return True
            
            if my_host != host: return True
            
            if my_port != port: return True
            
            return False
            
        
        def Update( self, contact ):
            
            ( public_key, name, host, port ) = contact.GetInfo()
            
            contact_key = contact.GetContactKey()
            
            self._name.SetValue( name )
            
            contact_address = host + ':' + str( port )
            
            if contact_key is not None: contact_address = contact_key.encode( 'hex' ) + '@' + contact_address
            
            self._contact_address.SetValue( contact_address )
            
            if public_key is None: public_key = ''
            
            self._public_key.SetValue( public_key )
            
        
    '''
class DialogManageExportFolders( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage export folders' )
        
        self._export_folders = ClientGUIListCtrl.BetterListCtrl( self, 'export_folders', 6, 40, [ ( 'name', 20 ), ( 'path', -1 ), ( 'type', 12 ), ( 'query', 16 ), ( 'period', 10 ), ( 'phrase', 20 ) ], self._ConvertExportFolderToListCtrlTuples, delete_key_callback = self.Delete, activation_callback = self.Edit )
        
        export_folders = HG.client_controller.Read( 'serialisable_named', HydrusSerialisable.SERIALISABLE_TYPE_EXPORT_FOLDER )
        
        self._export_folders.AddDatas( export_folders )
        
        self._add_button = wx.Button( self, label = 'add' )
        self._add_button.Bind( wx.EVT_BUTTON, self.EventAdd )
        
        self._edit_button = wx.Button( self, label = 'edit' )
        self._edit_button.Bind( wx.EVT_BUTTON, self.EventEdit )
        
        self._delete_button = wx.Button( self, label = 'delete' )
        self._delete_button.Bind( wx.EVT_BUTTON, self.EventDelete )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        file_buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        file_buttons.Add( self._add_button, CC.FLAGS_VCENTER )
        file_buttons.Add( self._edit_button, CC.FLAGS_VCENTER )
        file_buttons.Add( self._delete_button, CC.FLAGS_VCENTER )
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_VCENTER )
        buttons.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        intro = 'Here you can set the client to regularly export a certain query to a particular location.'
        
        vbox.Add( ClientGUICommon.BetterStaticText( self, intro ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._export_folders, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( file_buttons, CC.FLAGS_BUTTON_SIZER )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        if x < 780: x = 780
        if y < 480: y = 480
        
        self.SetInitialSize( ( x, y ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def _AddFolder( self ):
        
        new_options = HG.client_controller.new_options
        
        phrase = new_options.GetString( 'export_phrase' )
        
        name = 'export folder'
        path = ''
        export_type = HC.EXPORT_FOLDER_TYPE_REGULAR
        file_search_context = ClientSearch.FileSearchContext( file_service_key = CC.LOCAL_FILE_SERVICE_KEY )
        period = 15 * 60
        
        export_folder = ClientExporting.ExportFolder( name, path, export_type = export_type, file_search_context = file_search_context, period = period, phrase = phrase )
        
        with DialogManageExportFoldersEdit( self, export_folder ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                export_folder = dlg.GetInfo()
                
                export_folder.SetNonDupeName( self._GetExistingNames() )
                
                self._export_folders.AddDatas( ( export_folder, ) )
                
            
        
    
    def _ConvertExportFolderToListCtrlTuples( self, export_folder ):
        
        ( name, path, export_type, file_search_context, period, phrase ) = export_folder.ToTuple()
        
        if export_type == HC.EXPORT_FOLDER_TYPE_REGULAR:
            
            pretty_export_type = 'regular'
            
        elif export_type == HC.EXPORT_FOLDER_TYPE_SYNCHRONISE:
            
            pretty_export_type = 'synchronise'
            
        
        pretty_file_search_context = ', '.join( predicate.GetUnicode( with_count = False ) for predicate in file_search_context.GetPredicates() )
        
        pretty_period = HydrusData.TimeDeltaToPrettyTimeDelta( period )
        
        pretty_phrase = phrase
        
        display_tuple = ( name, path, pretty_export_type, pretty_file_search_context, pretty_period, pretty_phrase )
        
        sort_tuple = ( name, path, pretty_export_type, pretty_file_search_context, period, phrase )
        
        return ( display_tuple, sort_tuple )
        
    
    def _GetExistingNames( self ):
        
        existing_names = { export_folder.GetName() for export_folder in self._export_folders.GetData() }
        
        return existing_names
        
    
    def Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._export_folders.DeleteSelected()
                
            
        
    
    def Edit( self ):
        
        export_folders = self._export_folders.GetData( only_selected = True )
        
        for export_folder in export_folders:
            
            with DialogManageExportFoldersEdit( self, export_folder ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    self._export_folders.DeleteDatas( ( export_folder, ) )
                    
                    export_folder = dlg.GetInfo()
                    
                    export_folder.SetNonDupeName( self._GetExistingNames() )
                    
                    self._export_folders.AddDatas( ( export_folder, ) )
                    
                else:
                    
                    return
                    
                
            
        
    
    def EventAdd( self, event ):
        
        self._AddFolder()
        
    
    def EventDelete( self, event ):
        
        self.Delete()
        
    
    def EventEdit( self, event ):
        
        self.Edit()
        
    
    def EventOK( self, event ):
        
        existing_db_names = set( HG.client_controller.Read( 'serialisable_names', HydrusSerialisable.SERIALISABLE_TYPE_EXPORT_FOLDER ) )
        
        export_folders = self._export_folders.GetData()
        
        good_names = set()
        
        for export_folder in export_folders:
            
            HG.client_controller.Write( 'serialisable', export_folder )
            
            good_names.add( export_folder.GetName() )
            
        
        names_to_delete = existing_db_names - good_names
        
        for name in names_to_delete:
            
            HG.client_controller.Write( 'delete_serialisable_named', HydrusSerialisable.SERIALISABLE_TYPE_EXPORT_FOLDER, name )
            
        
        HG.client_controller.pub( 'notify_new_export_folders' )
        
        self.EndModal( wx.ID_OK )
        
    
class DialogManageExportFoldersEdit( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, export_folder ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'edit export folder' )
        
        self._export_folder = export_folder
        
        ( name, path, export_type, file_search_context, period, phrase ) = self._export_folder.ToTuple()
        
        self._path_box = ClientGUICommon.StaticBox( self, 'name and location' )
        
        self._name = wx.TextCtrl( self._path_box)
        
        self._path = wx.DirPickerCtrl( self._path_box, style = wx.DIRP_USE_TEXTCTRL )
        
        #
        
        self._type_box = ClientGUICommon.StaticBox( self, 'type of export' )
        
        self._type = ClientGUICommon.BetterChoice( self._type_box )
        self._type.Append( 'regular', HC.EXPORT_FOLDER_TYPE_REGULAR )
        self._type.Append( 'synchronise', HC.EXPORT_FOLDER_TYPE_SYNCHRONISE )
        
        #
        
        self._query_box = ClientGUICommon.StaticBox( self, 'query to export' )
        
        self._page_key = 'export folders placeholder'
        
        predicates = file_search_context.GetPredicates()
        
        self._predicates_box = ClientGUIListBoxes.ListBoxTagsActiveSearchPredicates( self._query_box, self._page_key, predicates )
        
        self._searchbox = ClientGUIACDropdown.AutoCompleteDropdownTagsRead( self._query_box, self._page_key, file_search_context )
        
        #
        
        self._period_box = ClientGUICommon.StaticBox( self, 'export period' )
        
        self._period = ClientGUITime.TimeDeltaButton( self._period_box, min = 3 * 60, days = True, hours = True, minutes = True )
        
        #
        
        self._phrase_box = ClientGUICommon.StaticBox( self, 'filenames' )
        
        self._pattern = wx.TextCtrl( self._phrase_box )
        
        self._examples = ClientGUICommon.ExportPatternButton( self._phrase_box )
        
        #
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        self._name.SetValue( name )
        
        self._path.SetPath( path )
        
        self._type.SelectClientData( export_type )
        
        self._period.SetValue( period )
        
        self._pattern.SetValue( phrase )
        
        #
        
        rows = []
        
        rows.append( ( 'name: ', self._name ) )
        rows.append( ( 'folder path: ', self._path ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._path_box, rows )
        
        self._path_box.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        text = '''regular - try to export the files to the directory, overwriting if the filesize if different

synchronise - try to export the files to the directory, overwriting if the filesize if different, and delete anything else in the directory

If you select synchronise, be careful!'''
        
        st = ClientGUICommon.BetterStaticText( self._type_box, label = text )
        
        st.SetWrapWidth( 440 )
        
        self._type_box.Add( st, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._type_box.Add( self._type, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self._query_box.Add( self._predicates_box, CC.FLAGS_EXPAND_BOTH_WAYS )
        self._query_box.Add( self._searchbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self._period_box.Add( self._period, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        phrase_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        phrase_hbox.Add( self._pattern, CC.FLAGS_EXPAND_BOTH_WAYS )
        phrase_hbox.Add( self._examples, CC.FLAGS_VCENTER )
        
        self._phrase_box.Add( phrase_hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_VCENTER )
        buttons.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._path_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._type_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._query_box, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( self._period_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._phrase_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        self.SetInitialSize( ( 480, y ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
        
    
    def EventOK( self, event ):
        
        if self._path.GetPath() in ( '', None ):
            
            wx.MessageBox( 'You must enter a folder path to export to!' )
            
            return
            
        
        phrase = self._pattern.GetValue()
        
        try:
            
            ClientExporting.ParseExportPhrase( phrase )
            
        except:
            
            wx.MessageBox( 'Could not parse that export phrase!' )
            
            return
            
        
        self.EndModal( wx.ID_OK )
        
    
    def GetInfo( self ):
        
        name = self._name.GetValue()
        
        path = HydrusData.ToUnicode( self._path.GetPath() )
        
        export_type = self._type.GetChoice()
        
        file_search_context = self._searchbox.GetFileSearchContext()
        
        predicates = self._predicates_box.GetPredicates()
        
        file_search_context.SetPredicates( predicates )
        
        period = self._period.GetValue()
        
        phrase = self._pattern.GetValue()
        
        export_folder = ClientExporting.ExportFolder( name, path, export_type, file_search_context, period, phrase )
        
        return export_folder
        
'''
class DialogManageImageboards( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        def InitialiseControls():
            
            self._sites = ClientGUICommon.ListBook( self )
            
            self._add = wx.Button( self, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
            self._add.SetForegroundColour( ( 0, 128, 0 ) )
            
            self._remove = wx.Button( self, label = 'remove' )
            self._remove.Bind( wx.EVT_BUTTON, self.EventRemove )
            self._remove.SetForegroundColour( ( 128, 0, 0 ) )
            
            self._export = wx.Button( self, label = 'export' )
            self._export.Bind( wx.EVT_BUTTON, self.EventExport )
            
            self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
            self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
            self._ok.SetForegroundColour( ( 0, 128, 0 ) )
            
            self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
            self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
            
        
        def PopulateControls():
            
            self._names_to_delete = []
            
            sites = HG.client_controller.Read( 'imageboards' )
            
            for ( name, imageboards ) in sites.items():
                
                self._sites.AddPageArgs( name, name, self._Panel, ( self._sites, imageboards ), {} )
                
            
        
        def ArrangeControls():
            
            add_remove_hbox = wx.BoxSizer( wx.HORIZONTAL )
            add_remove_hbox.Add( self._add, CC.FLAGS_VCENTER )
            add_remove_hbox.Add( self._remove, CC.FLAGS_VCENTER )
            add_remove_hbox.Add( self._export, CC.FLAGS_VCENTER )
            
            ok_hbox = wx.BoxSizer( wx.HORIZONTAL )
            ok_hbox.Add( self._ok, CC.FLAGS_VCENTER )
            ok_hbox.Add( self._cancel, CC.FLAGS_VCENTER )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            vbox.Add( self._sites, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.Add( add_remove_hbox, CC.FLAGS_SMALL_INDENT )
            vbox.Add( ok_hbox, CC.FLAGS_BUTTON_SIZER )
            
            self.SetSizer( vbox )
            
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage imageboards' )
        
        InitialiseControls()
        
        PopulateControls()
        
        ArrangeControls()
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        self.SetInitialSize( ( 980, y ) )
        
        self.SetDropTarget( ClientDragDrop.FileDropTarget( filenames_callable = self.Import ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def EventAdd( self, event ):
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter new site\'s name.' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                try:
                    
                    name = dlg.GetValue()
                    
                    if self._sites.KeyExists( name ): raise HydrusExceptions.NameException( 'That name is already in use!' )
                    
                    if name == '': raise HydrusExceptions.NameException( 'Please enter a nickname for the service.' )
                    
                    page = self._Panel( self._sites, [], is_new = True )
                    
                    self._sites.AddPage( name, name, page, select = True )
                    
                except HydrusExceptions.NameException as e:
                    
                    wx.MessageBox( HydrusData.ToUnicode( e ) )
                    
                    self.EventAdd( event )
                    
                
            
        
    
    def EventExport( self, event ):
        
        site_panel = self._sites.GetCurrentPage()
        
        if site_panel is not None:
            
            name = self._sites.GetCurrentKey()
            
            imageboards = site_panel.GetImageboards()
            
            dict = { name : imageboards }
            
            with wx.FileDialog( self, 'select where to export site', defaultFile = 'site.yaml', style = wx.FD_SAVE ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    path = HydrusData.ToUnicode( dlg.GetPath() )
                    
                    with open( path, 'wb' ) as f: f.write( yaml.safe_dump( dict ) )
                    
                
            
        
    
    def EventOK( self, event ):
        
        try:
            
            for name in self._names_to_delete:
                
                HG.client_controller.Write( 'delete_imageboard', name )
                
            
            for page in self._sites.GetActivePages():
                
                if page.HasChanges():
                    
                    imageboards = page.GetImageboards()
                    
                    name = 'this is old code'
                    
                    HG.client_controller.Write( 'imageboard', name, imageboards )
                    
                
            
        finally: self.EndModal( wx.ID_OK )
        
    
    def EventRemove( self, event ):
        
        site_panel = self._sites.GetCurrentPage()
        
        if site_panel is not None:
            
            name = self._sites.GetCurrentKey()
            
            self._names_to_delete.append( name )
            
            self._sites.DeleteCurrentPage()
            
        
    
    def Import( self, paths ):
        
        for path in paths:
            
            try:
                
                with open( path, 'rb' ) as f: file = f.read()
                
                thing = yaml.safe_load( file )
                
                if isinstance( thing, dict ):
                    
                    ( name, imageboards ) = thing.items()[0]
                    
                    if not self._sites.KeyExists( name ):
                        
                        page = self._Panel( self._sites, [], is_new = True )
                        
                        self._sites.AddPage( name, name, page, select = True )
                        
                    
                    page = self._sites.GetPage( name )
                    
                    for imageboard in imageboards:
                        
                        if isinstance( imageboard, ClientData.Imageboard ): page.UpdateImageboard( imageboard )
                        
                    
                elif isinstance( thing, ClientData.Imageboard ):
                    
                    imageboard = thing
                    
                    page = self._sites.GetCurrentPage()
                    
                    page.UpdateImageboard( imageboard )
                    
                
            except:
                
                wx.MessageBox( traceback.format_exc() )
                
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, imageboards, is_new = False ):
            
            def InitialiseControls():
                
                self._site_panel = ClientGUICommon.StaticBox( self, 'site' )
                
                self._imageboards = ClientGUICommon.ListBook( self._site_panel )
                
                self._add = wx.Button( self._site_panel, label = 'add' )
                self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
                self._add.SetForegroundColour( ( 0, 128, 0 ) )
                
                self._remove = wx.Button( self._site_panel, label = 'remove' )
                self._remove.Bind( wx.EVT_BUTTON, self.EventRemove )
                self._remove.SetForegroundColour( ( 128, 0, 0 ) )
                
                self._export = wx.Button( self._site_panel, label = 'export' )
                self._export.Bind( wx.EVT_BUTTON, self.EventExport )
                
            
            def PopulateControls():
                
                for imageboard in imageboards:
                    
                    name = imageboard.GetName()
                    
                    self._imageboards.AddPageArgs( name, name, self._Panel, ( self._imageboards, imageboard ), {} )
                    
                
            
            def ArrangeControls():
                
                add_remove_hbox = wx.BoxSizer( wx.HORIZONTAL )
                add_remove_hbox.Add( self._add, CC.FLAGS_VCENTER )
                add_remove_hbox.Add( self._remove, CC.FLAGS_VCENTER )
                add_remove_hbox.Add( self._export, CC.FLAGS_VCENTER )
                
                self._site_panel.Add( self._imageboards, CC.FLAGS_EXPAND_BOTH_WAYS )
                self._site_panel.Add( add_remove_hbox, CC.FLAGS_SMALL_INDENT )
                
                vbox = wx.BoxSizer( wx.VERTICAL )
                
                vbox.Add( self._site_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                
                self.SetSizer( vbox )
                
            
            wx.Panel.__init__( self, parent )
            
            self._original_imageboards = imageboards
            self._has_changes = False
            self._is_new = is_new
            
            InitialiseControls()
            
            PopulateControls()
            
            ArrangeControls()
        
            ( x, y ) = self.GetEffectiveMinSize()
            
            self.SetInitialSize( ( 980, y ) )
            
        
        def EventAdd( self, event ):
            
            with ClientGUIDialogs.DialogTextEntry( self, 'Enter new imageboard\'s name.' ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    try:
                        
                        name = dlg.GetValue()
                        
                        if self._imageboards.KeyExists( name ): raise HydrusExceptions.NameException()
                        
                        if name == '': raise Exception( 'Please enter a nickname for the service.' )
                        
                        imageboard = ClientData.Imageboard( name, '', 60, [], {} )
                        
                        page = self._Panel( self._imageboards, imageboard, is_new = True )
                        
                        self._imageboards.AddPage( name, name, page, select = True )
                        
                        self._has_changes = True
                        
                    except Exception as e:
                        
                        wx.MessageBox( HydrusData.ToUnicode( e ) )
                        
                        self.EventAdd( event )
                        
                    
                
            
        
        def EventExport( self, event ):
            
            imageboard_panel = self._imageboards.GetCurrentPage()
            
            if imageboard_panel is not None:
                
                imageboard = imageboard_panel.GetImageboard()
                
                with wx.FileDialog( self, 'select where to export imageboard', defaultFile = 'imageboard.yaml', style = wx.FD_SAVE ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        path = HydrusData.ToUnicode( dlg.GetPath() )
                        
                        with open( path, 'wb' ) as f: f.write( yaml.safe_dump( imageboard ) )
                        
                    
                
            
        
        def EventRemove( self, event ):
            
            imageboard_panel = self._imageboards.GetCurrentPage()
            
            if imageboard_panel is not None:
                
                name = self._imageboards.GetCurrentKey()
                
                self._imageboards.DeleteCurrentPage()
                
                self._has_changes = True
                
            
        
        def GetImageboards( self ):
            
            names_to_imageboards = { imageboard.GetName() : imageboard for imageboard in self._original_imageboards if self._imageboards.KeyExists( imageboard.GetName() ) }
            
            for page in self._imageboards.GetActivePages():
                
                imageboard = page.GetImageboard()
                
                names_to_imageboards[ imageboard.GetName() ] = imageboard
                
            
            return names_to_imageboards.values()
            
        
        def HasChanges( self ):
            
            if self._is_new: return True
            
            return self._has_changes or True in ( page.HasChanges() for page in self._imageboards.GetActivePages() )
            
        
        def UpdateImageboard( self, imageboard ):
            
            name = imageboard.GetName()
            
            if not self._imageboards.KeyExists( name ):
                
                new_imageboard = ClientData.Imageboard( name, '', 60, [], {} )
                
                page = self._Panel( self._imageboards, new_imageboard, is_new = True )
                
                self._imageboards.AddPage( name, name, page, select = True )
                
            
            page = self._imageboards.GetPage( name )
            
            page.Update( imageboard )
            
        
        class _Panel( wx.Panel ):
            
            def __init__( self, parent, imageboard, is_new = False ):
                
                wx.Panel.__init__( self, parent )
                
                self._imageboard = imageboard
                self._is_new = is_new
                
                ( post_url, flood_time, form_fields, restrictions ) = self._imageboard.GetBoardInfo()
                
                def InitialiseControls():
                    
                    self._imageboard_panel = ClientGUICommon.StaticBox( self, 'imageboard' )
                    
                    #
                    
                    self._basic_info_panel = ClientGUICommon.StaticBox( self._imageboard_panel, 'basic info' )
                    
                    self._post_url = wx.TextCtrl( self._basic_info_panel )
                    
                    self._flood_time = wx.SpinCtrl( self._basic_info_panel, min = 5, max = 1200 )
                    
                    #
                    
                    self._form_fields_panel = ClientGUICommon.StaticBox( self._imageboard_panel, 'form fields' )
                    
                    self._form_fields = ClientGUICommon.SaneListCtrl( self._form_fields_panel, 350, [ ( 'name', 120 ), ( 'type', 120 ), ( 'default', -1 ), ( 'editable', 120 ) ], delete_key_callback = self.Delete )
                    
                    self._add = wx.Button( self._form_fields_panel, label = 'add' )
                    self._add.Bind( wx.EVT_BUTTON, self.EventAdd )
                    
                    self._edit = wx.Button( self._form_fields_panel, label = 'edit' )
                    self._edit.Bind( wx.EVT_BUTTON, self.EventEdit )
                    
                    self._delete = wx.Button( self._form_fields_panel, label = 'delete' )
                    self._delete.Bind( wx.EVT_BUTTON, self.EventDelete )
                    
                    #
                    
                    self._restrictions_panel = ClientGUICommon.StaticBox( self._imageboard_panel, 'restrictions' )
                    
                    self._min_resolution = ClientGUICommon.NoneableSpinCtrl( self._restrictions_panel, 'min resolution', num_dimensions = 2 )
                    
                    self._max_resolution = ClientGUICommon.NoneableSpinCtrl( self._restrictions_panel, 'max resolution', num_dimensions = 2 )
                    
                    self._max_file_size = ClientGUICommon.NoneableSpinCtrl( self._restrictions_panel, 'max file size (KB)', multiplier = 1024 )
                    
                    self._allowed_mimes_panel = ClientGUICommon.StaticBox( self._restrictions_panel, 'allowed mimes' )
                    
                    self._mimes = wx.ListBox( self._allowed_mimes_panel )
                    
                    self._mime_choice = wx.Choice( self._allowed_mimes_panel )
                    
                    self._add_mime = wx.Button( self._allowed_mimes_panel, label = 'add' )
                    self._add_mime.Bind( wx.EVT_BUTTON, self.EventAddMime )
                    
                    self._remove_mime = wx.Button( self._allowed_mimes_panel, label = 'remove' )
                    self._remove_mime.Bind( wx.EVT_BUTTON, self.EventRemoveMime )
                    
                
                def PopulateControls():
                    
                    #
                    
                    self._post_url.SetValue( post_url )
                    
                    self._flood_time.SetRange( 5, 1200 )
                    self._flood_time.SetValue( flood_time )
                    
                    #
                    
                    for ( name, field_type, default, editable ) in form_fields:
                        
                        self._form_fields.Append( ( name, CC.field_string_lookup[ field_type ], HydrusData.ToUnicode( default ), HydrusData.ToUnicode( editable ) ), ( name, field_type, default, editable ) )
                        
                    
                    #
                    
                    if CC.RESTRICTION_MIN_RESOLUTION in restrictions: value = restrictions[ CC.RESTRICTION_MIN_RESOLUTION ]
                    else: value = None
                    
                    self._min_resolution.SetValue( value )
                    
                    if CC.RESTRICTION_MAX_RESOLUTION in restrictions: value = restrictions[ CC.RESTRICTION_MAX_RESOLUTION ]
                    else: value = None
                    
                    self._max_resolution.SetValue( value )
                    
                    if CC.RESTRICTION_MAX_FILE_SIZE in restrictions: value = restrictions[ CC.RESTRICTION_MAX_FILE_SIZE ]
                    else: value = None
                    
                    self._max_file_size.SetValue( value )
                    
                    if CC.RESTRICTION_ALLOWED_MIMES in restrictions: mimes = restrictions[ CC.RESTRICTION_ALLOWED_MIMES ]
                    else: mimes = []
                    
                    for mime in mimes: self._mimes.Append( HC.mime_string_lookup[ mime ], mime )
                    
                    for mime in HC.ALLOWED_MIMES: self._mime_choice.Append( HC.mime_string_lookup[ mime ], mime )
                    
                    self._mime_choice.SetSelection( 0 )
                    
                
                def ArrangeControls():
                    
                    gridbox = wx.FlexGridSizer( 2 )
                    
                    gridbox.AddGrowableCol( 1, 1 )
                    
                    gridbox.Add( wx.StaticText( self._basic_info_panel, label = 'POST URL' ), CC.FLAGS_VCENTER )
                    gridbox.Add( self._post_url, CC.FLAGS_EXPAND_BOTH_WAYS )
                    gridbox.Add( wx.StaticText( self._basic_info_panel, label = 'flood time' ), CC.FLAGS_VCENTER )
                    gridbox.Add( self._flood_time, CC.FLAGS_EXPAND_BOTH_WAYS )
                    
                    self._basic_info_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
                    
                    #
                    
                    h_b_box = wx.BoxSizer( wx.HORIZONTAL )
                    h_b_box.Add( self._add, CC.FLAGS_VCENTER )
                    h_b_box.Add( self._edit, CC.FLAGS_VCENTER )
                    h_b_box.Add( self._delete, CC.FLAGS_VCENTER )
                    
                    self._form_fields_panel.Add( self._form_fields, CC.FLAGS_EXPAND_BOTH_WAYS )
                    self._form_fields_panel.Add( h_b_box, CC.FLAGS_BUTTON_SIZER )
                    
                    #
                    
                    mime_buttons_box = wx.BoxSizer( wx.HORIZONTAL )
                    mime_buttons_box.Add( self._mime_choice, CC.FLAGS_VCENTER )
                    mime_buttons_box.Add( self._add_mime, CC.FLAGS_VCENTER )
                    mime_buttons_box.Add( self._remove_mime, CC.FLAGS_VCENTER )
                    
                    self._allowed_mimes_panel.Add( self._mimes, CC.FLAGS_EXPAND_BOTH_WAYS )
                    self._allowed_mimes_panel.Add( mime_buttons_box, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
                    
                    self._restrictions_panel.Add( self._min_resolution, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._restrictions_panel.Add( self._max_resolution, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._restrictions_panel.Add( self._max_file_size, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._restrictions_panel.Add( self._allowed_mimes_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                    
                    #
                    
                    self._imageboard_panel.Add( self._basic_info_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
                    self._imageboard_panel.Add( self._form_fields_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                    self._imageboard_panel.Add( self._restrictions_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
                    
                    vbox = wx.BoxSizer( wx.VERTICAL )
                    
                    vbox.Add( self._imageboard_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
                    
                    self.SetSizer( vbox )
                    
                
                InitialiseControls()
                
                PopulateControls()
                
                ArrangeControls()
                
            
            def _GetInfo( self ):
                
                imageboard_name = self._imageboard.GetName()
                
                post_url = self._post_url.GetValue()
                
                flood_time = self._flood_time.GetValue()
                
                form_fields = self._form_fields.GetClientData()
                
                restrictions = {}
                
                value = self._min_resolution.GetValue()
                if value is not None: restrictions[ CC.RESTRICTION_MIN_RESOLUTION ] = value
                
                value = self._max_resolution.GetValue()
                if value is not None: restrictions[ CC.RESTRICTION_MAX_RESOLUTION ] = value
                
                value = self._max_file_size.GetValue()
                if value is not None: restrictions[ CC.RESTRICTION_MAX_FILE_SIZE ] = value
                
                mimes = [ self._mimes.GetClientData( i ) for i in range( self._mimes.GetCount() ) ]
                
                if len( mimes ) > 0: restrictions[ CC.RESTRICTION_ALLOWED_MIMES ] = mimes
                
                return ( imageboard_name, post_url, flood_time, form_fields, restrictions )
                
            
            def Delete( self ): self._form_fields.RemoveAllSelected()
            
            def EventAdd( self, event ):
                
                with ClientGUIDialogs.DialogInputNewFormField( self ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_OK:
                        
                        ( name, field_type, default, editable ) = dlg.GetFormField()
                        
                        if name in [ form_field[0] for form_field in self._form_fields.GetClientData() ]:
                            
                            wx.MessageBox( 'There is already a field named ' + name )
                            
                            self.EventAdd( event )
                            
                            return
                            
                        
                        self._form_fields.Append( ( name, CC.field_string_lookup[ field_type ], HydrusData.ToUnicode( default ), HydrusData.ToUnicode( editable ) ), ( name, field_type, default, editable ) )
                        
                    
                
            
            def EventAddMime( self, event ):
                
                selection = self._mime_choice.GetSelection()
                
                if selection != wx.NOT_FOUND:
                    
                    mime = self._mime_choice.GetClientData( selection )
                    
                    existing_mimes = [ self._mimes.GetClientData( i ) for i in range( self._mimes.GetCount() ) ]
                    
                    if mime not in existing_mimes: self._mimes.Append( HC.mime_string_lookup[ mime ], mime )
                    
                
            
            def EventDelete( self, event ): self.Delete()
            
            def EventRemoveMime( self, event ):
                
                selection = self._mimes.GetSelection()
                
                if selection != wx.NOT_FOUND: self._mimes.Delete( selection )
                
            
            def EventEdit( self, event ):
                
                indices = self._form_fields.GetAllSelected()
                
                for index in indices:
                    
                    ( name, field_type, default, editable ) = self._form_fields.GetClientData( index )
                    
                    form_field = ( name, field_type, default, editable )
                    
                    with ClientGUIDialogs.DialogInputNewFormField( self, form_field ) as dlg:
                        
                        if dlg.ShowModal() == wx.ID_OK:
                            
                            old_name = name
                            
                            ( name, field_type, default, editable ) = dlg.GetFormField()
                            
                            if old_name != name:
                                
                                if name in [ form_field[0] for form_field in self._form_fields.GetClientData() ]: raise Exception( 'You already have a form field called ' + name + '; delete or edit that one first' )
                                
                            
                            self._form_fields.UpdateRow( index, ( name, CC.field_string_lookup[ field_type ], HydrusData.ToUnicode( default ), HydrusData.ToUnicode( editable ) ), ( name, field_type, default, editable ) )
                            
                        
                    
                
            
            def GetImageboard( self ):
                
                ( name, post_url, flood_time, form_fields, restrictions ) = self._GetInfo()
                
                return ClientData.Imageboard( name, post_url, flood_time, form_fields, restrictions )
                
            
            def HasChanges( self ):
                
                if self._is_new: return True
                
                ( my_name, my_post_url, my_flood_time, my_form_fields, my_restrictions ) = self._GetInfo()
                
                ( post_url, flood_time, form_fields, restrictions ) = self._imageboard.GetBoardInfo()
                
                if post_url != my_post_url: return True
                
                if flood_time != my_flood_time: return True
                
                if set( [ tuple( item ) for item in form_fields ] ) != set( [ tuple( item ) for item in my_form_fields ] ): return True
                
                if restrictions != my_restrictions: return True
                
                return False
                
            
            def Update( self, imageboard ):
                
                ( post_url, flood_time, form_fields, restrictions ) = imageboard.GetBoardInfo()
                
                self._post_url.SetValue( post_url )
                self._flood_time.SetValue( flood_time )
                
                self._form_fields.ClearAll()
                
                self._form_fields.InsertColumn( 0, 'name', width = 120 )
                self._form_fields.InsertColumn( 1, 'type', width = 120 )
                self._form_fields.InsertColumn( 2, 'default' )
                self._form_fields.InsertColumn( 3, 'editable', width = 120 )
                
                self._form_fields.setResizeColumn( 3 ) # default
                
                for ( name, field_type, default, editable ) in form_fields:
                    
                    self._form_fields.Append( ( name, CC.field_string_lookup[ field_type ], HydrusData.ToUnicode( default ), HydrusData.ToUnicode( editable ) ), ( name, field_type, default, editable ) )
                    
                
                if CC.RESTRICTION_MIN_RESOLUTION in restrictions: value = restrictions[ CC.RESTRICTION_MIN_RESOLUTION ]
                else: value = None
                
                self._min_resolution.SetValue( value )
                
                if CC.RESTRICTION_MAX_RESOLUTION in restrictions: value = restrictions[ CC.RESTRICTION_MAX_RESOLUTION ]
                else: value = None
                
                self._max_resolution.SetValue( value )
                
                if CC.RESTRICTION_MAX_FILE_SIZE in restrictions: value = restrictions[ CC.RESTRICTION_MAX_FILE_SIZE ]
                else: value = None
                
                self._max_file_size.SetValue( value )
                
                self._mimes.Clear()
                
                if CC.RESTRICTION_ALLOWED_MIMES in restrictions: mimes = restrictions[ CC.RESTRICTION_ALLOWED_MIMES ]
                else: mimes = []
                
                for mime in mimes: self._mimes.Append( HC.mime_string_lookup[ mime ], mime )
                
            
        
'''
class DialogManageImportFolders( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage import folders' )
        
        self._import_folders = ClientGUIListCtrl.SaneListCtrlForSingleObject( self, 120, [ ( 'name', 120 ), ( 'path', -1 ), ( 'check period', 120 ) ], delete_key_callback = self.Delete, activation_callback = self.Edit )
        
        self._add_button = wx.Button( self, label = 'add' )
        self._add_button.Bind( wx.EVT_BUTTON, self.EventAdd )
        
        self._edit_button = wx.Button( self, label = 'edit' )
        self._edit_button.Bind( wx.EVT_BUTTON, self.EventEdit )
        
        self._delete_button = wx.Button( self, label = 'delete' )
        self._delete_button.Bind( wx.EVT_BUTTON, self.EventDelete )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        import_folders = HG.client_controller.Read( 'serialisable_named', HydrusSerialisable.SERIALISABLE_TYPE_IMPORT_FOLDER )
        
        for import_folder in import_folders:
            
            ( display_tuple, sort_tuple ) = self._ConvertImportFolderToTuples( import_folder )
            
            self._import_folders.Append( display_tuple, sort_tuple, import_folder )
            
        
        #
        
        file_buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        file_buttons.Add( self._add_button, CC.FLAGS_VCENTER )
        file_buttons.Add( self._edit_button, CC.FLAGS_VCENTER )
        file_buttons.Add( self._delete_button, CC.FLAGS_VCENTER )
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_VCENTER )
        buttons.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        intro = 'Here you can set the client to regularly check certain folders for new files to import.'
        
        vbox.Add( ClientGUICommon.BetterStaticText( self, intro ), CC.FLAGS_EXPAND_PERPENDICULAR )
        
        warning = 'WARNING: Import folders check (and potentially move/delete!) the contents of all subdirectories as well as the base directory!'
        
        warning_st = ClientGUICommon.BetterStaticText( self, warning )
        
        warning_st.SetForegroundColour( ( 128, 0, 0 ) )
        
        vbox.Add( warning_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._import_folders, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( file_buttons, CC.FLAGS_BUTTON_SIZER )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        #
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        if x < 780: x = 780
        if y < 480: y = 480
        
        self.SetInitialSize( ( x, y ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def _AddImportFolder( self ):
        
        import_folder = ClientImporting.ImportFolder( 'import folder' )
        
        with DialogManageImportFoldersEdit( self, import_folder ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                import_folder = dlg.GetInfo()
                
                self._import_folders.SetNonDupeName( import_folder )
                
                ( display_tuple, sort_tuple ) = self._ConvertImportFolderToTuples( import_folder )
                
                self._import_folders.Append( display_tuple, sort_tuple, import_folder )
                
            
        
    
    def _ConvertImportFolderToTuples( self, import_folder ):
        
        sort_tuple = import_folder.ToListBoxTuple()
        
        ( name, path, check_period ) = sort_tuple
        
        pretty_check_period = HydrusData.TimeDeltaToPrettyTimeDelta( check_period )
        
        display_tuple = ( name, path, pretty_check_period )
        
        return ( display_tuple, sort_tuple )
        
    
    def Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._import_folders.RemoveAllSelected()
                
            
        
    
    def Edit( self ):
        
        indices = self._import_folders.GetAllSelected()
        
        for index in indices:
            
            import_folder = self._import_folders.GetObject( index )
            
            original_name = import_folder.GetName()
            
            with DialogManageImportFoldersEdit( self, import_folder ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    import_folder = dlg.GetInfo()
                    
                    if import_folder.GetName() != original_name:
                        
                        self._import_folders.SetNonDupeName( import_folder )
                        
                    
                    ( display_tuple, sort_tuple ) = self._ConvertImportFolderToTuples( import_folder )
                    
                    self._import_folders.UpdateRow( index, display_tuple, sort_tuple, import_folder )
                    
                
            
        
    
    def EventAdd( self, event ):
        
        self._AddImportFolder()
        
    
    def EventDelete( self, event ):
        
        self.Delete()
        
    
    def EventEdit( self, event ):
        
        self.Edit()
        
    
    def EventOK( self, event ):
        
        existing_db_names = set( HG.client_controller.Read( 'serialisable_names', HydrusSerialisable.SERIALISABLE_TYPE_IMPORT_FOLDER ) )
        
        good_names = set()
        
        import_folders = self._import_folders.GetObjects()
        
        for import_folder in import_folders:
            
            good_names.add( import_folder.GetName() )
            
            HG.client_controller.Write( 'serialisable', import_folder )
            
        
        names_to_delete = existing_db_names - good_names
        
        for name in names_to_delete:
            
            HG.client_controller.Write( 'delete_serialisable_named', HydrusSerialisable.SERIALISABLE_TYPE_IMPORT_FOLDER, name )
            
        
        HG.client_controller.pub( 'notify_new_import_folders' )
        
        self.EndModal( wx.ID_OK )
        
    
class DialogManageImportFoldersEdit( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, import_folder ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'edit import folder' )
        
        self._import_folder = import_folder
        
        ( name, path, mimes, file_import_options, tag_import_options, tag_service_keys_to_filename_tagging_options, actions, action_locations, period, check_regularly, paused, check_now, show_working_popup, publish_files_to_popup_button, publish_files_to_page ) = self._import_folder.ToTuple()
        
        self._panel = wx.ScrolledWindow( self )
        
        self._folder_box = ClientGUICommon.StaticBox( self._panel, 'folder options' )
        
        self._name = wx.TextCtrl( self._folder_box )
        
        self._path = wx.DirPickerCtrl( self._folder_box, style = wx.DIRP_USE_TEXTCTRL )
        
        self._check_regularly = wx.CheckBox( self._folder_box )
        
        self._period = ClientGUITime.TimeDeltaButton( self._folder_box, min = 3 * 60, days = True, hours = True, minutes = True )
        
        self._paused = wx.CheckBox( self._folder_box )
        
        self._check_now = wx.CheckBox( self._folder_box )
        
        self._show_working_popup = wx.CheckBox( self._folder_box )
        self._publish_files_to_popup_button = wx.CheckBox( self._folder_box )
        self._publish_files_to_page = wx.CheckBox( self._folder_box )
        
        self._file_seed_cache_button = ClientGUIFileSeedCache.FileSeedCacheButton( self._folder_box, HG.client_controller, self._import_folder.GetFileSeedCache, file_seed_cache_set_callable = self._import_folder.SetFileSeedCache )
        
        #
        
        self._file_box = ClientGUICommon.StaticBox( self._panel, 'file options' )
        
        self._mimes = ClientGUIOptionsPanels.OptionsPanelMimes( self._file_box, HC.ALLOWED_MIMES )
        
        def create_choice():
            
            choice = ClientGUICommon.BetterChoice( self._file_box )
            
            for if_id in ( CC.IMPORT_FOLDER_DELETE, CC.IMPORT_FOLDER_IGNORE, CC.IMPORT_FOLDER_MOVE ):
                
                choice.Append( CC.import_folder_string_lookup[ if_id ], if_id )
                
            
            choice.Bind( wx.EVT_CHOICE, self.EventCheckLocations )
            
            return choice
            
        
        self._action_successful = create_choice()
        self._location_successful = wx.DirPickerCtrl( self._file_box, style = wx.DIRP_USE_TEXTCTRL )
        
        self._action_redundant = create_choice()
        self._location_redundant = wx.DirPickerCtrl( self._file_box, style = wx.DIRP_USE_TEXTCTRL )
        
        self._action_deleted = create_choice()
        self._location_deleted = wx.DirPickerCtrl( self._file_box, style = wx.DIRP_USE_TEXTCTRL )
        
        self._action_failed = create_choice()
        self._location_failed = wx.DirPickerCtrl( self._file_box, style = wx.DIRP_USE_TEXTCTRL )
        
        self._file_import_options = ClientGUIImport.FileImportOptionsButton( self._file_box, file_import_options )
        
        #
        
        self._tag_box = ClientGUICommon.StaticBox( self._panel, 'tag options' )
        
        self._tag_import_options = ClientGUIImport.TagImportOptionsButton( self._tag_box, [], tag_import_options, show_downloader_options = False )
        
        filename_tagging_options_panel = ClientGUIListCtrl.BetterListCtrlPanel( self._tag_box )
        
        self._filename_tagging_options = ClientGUIListCtrl.BetterListCtrl( filename_tagging_options_panel, 'filename_tagging_options', 5, 25, [ ( 'filename tagging options services', -1 ) ], self._ConvertFilenameTaggingOptionsToListctrlTuple, delete_key_callback = self._DeleteFilenameTaggingOptions, activation_callback = self._EditFilenameTaggingOptions )
        
        filename_tagging_options_panel.SetListCtrl( self._filename_tagging_options )
        
        filename_tagging_options_panel.AddButton( 'add', self._AddFilenameTaggingOptions )
        filename_tagging_options_panel.AddButton( 'edit', self._EditFilenameTaggingOptions, enabled_only_on_selection = True )
        filename_tagging_options_panel.AddButton( 'delete', self._DeleteFilenameTaggingOptions, enabled_only_on_selection = True )
        
        services_manager = HG.client_controller.services_manager
        
        #
        
        self._ok = wx.Button( self, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        self._name.SetValue( name )
        self._path.SetPath( path )
        
        self._check_regularly.SetValue( check_regularly )
        
        self._period.SetValue( period )
        self._paused.SetValue( paused )
        
        self._show_working_popup.SetValue( show_working_popup )
        self._publish_files_to_popup_button.SetValue( publish_files_to_popup_button )
        self._publish_files_to_page.SetValue( publish_files_to_page )
        
        self._mimes.SetValue( mimes )
        
        self._action_successful.SelectClientData( actions[ CC.STATUS_SUCCESSFUL_AND_NEW ] )
        if CC.STATUS_SUCCESSFUL_AND_NEW in action_locations:
            
            self._location_successful.SetPath( action_locations[ CC.STATUS_SUCCESSFUL_AND_NEW ] )
            
        
        self._action_redundant.SelectClientData( actions[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] )
        if CC.STATUS_SUCCESSFUL_BUT_REDUNDANT in action_locations:
            
            self._location_redundant.SetPath( action_locations[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] )
            
        
        self._action_deleted.SelectClientData( actions[ CC.STATUS_DELETED ] )
        if CC.STATUS_DELETED in action_locations:
            
            self._location_deleted.SetPath( action_locations[ CC.STATUS_DELETED ] )
            
        
        self._action_failed.SelectClientData( actions[ CC.STATUS_ERROR ] )
        if CC.STATUS_ERROR in action_locations:
            
            self._location_failed.SetPath( action_locations[ CC.STATUS_ERROR ] )
            
        
        good_tag_service_keys_to_filename_tagging_options = { service_key : filename_tagging_options for ( service_key, filename_tagging_options ) in tag_service_keys_to_filename_tagging_options.items() if HG.client_controller.services_manager.ServiceExists( service_key ) }
        
        self._filename_tagging_options.AddDatas( good_tag_service_keys_to_filename_tagging_options.items() )
        
        self._filename_tagging_options.Sort()
        
        #
        
        rows = []
        
        rows.append( ( 'name: ', self._name ) )
        rows.append( ( 'folder path: ', self._path ) )
        rows.append( ( 'currently paused (if set, will not ever do any work): ', self._paused ) )
        rows.append( ( 'check regularly?: ', self._check_regularly ) )
        rows.append( ( 'check period: ', self._period ) )
        rows.append( ( 'check on manage dialog ok: ', self._check_now ) )
        rows.append( ( 'show a popup while working: ', self._show_working_popup ) )
        rows.append( ( 'if new files imported, publish them to a popup button: ', self._publish_files_to_popup_button ) )
        rows.append( ( 'if new files imported, publish them to a page: ', self._publish_files_to_page ) )
        rows.append( ( 'review currently cached import paths: ', self._file_seed_cache_button ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._folder_box, rows )
        
        self._folder_box.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'mimes to import: ', self._mimes ) )
        
        mimes_gridbox = ClientGUICommon.WrapInGrid( self._file_box, rows, expand_text = True )
        
        gridbox = wx.FlexGridSizer( 3 )
        
        gridbox.AddGrowableCol( 1, 1 )
        
        gridbox.Add( wx.StaticText( self._file_box, label = 'when a file imports successfully: '), CC.FLAGS_VCENTER )
        gridbox.Add( self._action_successful, CC.FLAGS_EXPAND_BOTH_WAYS )
        gridbox.Add( self._location_successful, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        gridbox.Add( wx.StaticText( self._file_box, label = 'when a file is already in the db: '), CC.FLAGS_VCENTER )
        gridbox.Add( self._action_redundant, CC.FLAGS_EXPAND_BOTH_WAYS )
        gridbox.Add( self._location_redundant, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        gridbox.Add( wx.StaticText( self._file_box, label = 'when a file has previously been deleted from the db: '), CC.FLAGS_VCENTER )
        gridbox.Add( self._action_deleted, CC.FLAGS_EXPAND_BOTH_WAYS )
        gridbox.Add( self._location_deleted, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        gridbox.Add( wx.StaticText( self._file_box, label = 'when a file fails to import: '), CC.FLAGS_VCENTER )
        gridbox.Add( self._action_failed, CC.FLAGS_EXPAND_BOTH_WAYS )
        gridbox.Add( self._location_failed, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self._file_box.Add( mimes_gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        self._file_box.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        self._file_box.Add( self._file_import_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        #
        
        self._tag_box.Add( self._tag_import_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._tag_box.Add( filename_tagging_options_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        #
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_VCENTER )
        buttons.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._folder_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._file_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._tag_box, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self._panel.SetSizer( vbox )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        ( max_x, max_y ) = ClientGUITopLevelWindows.GetDisplaySize( self )
        
        x = min( x + 25, max_x )
        y = min( y + 25, max_y )
        
        self._panel.SetScrollRate( 20, 20 )
        
        self.SetInitialSize( ( x, y ) )
        
        self._CheckLocations()
        
        self._check_regularly.Bind( wx.EVT_CHECKBOX, self.EventCheckRegularly )
        
        self._UpdateCheckRegularly()
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def _AddFilenameTaggingOptions( self ):
        
        service_key = ClientGUIDialogs.SelectServiceKey( HC.TAG_SERVICES )
        
        if service_key is None:
            
            return
            
        
        existing_service_keys = { service_key for ( service_key, filename_tagging_options ) in self._filename_tagging_options.GetData() }
        
        if service_key in existing_service_keys:
            
            wx.MessageBox( 'You already have an entry for that service key! Please try editing it instead!' )
            
            return
            
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit filename tagging options' ) as dlg:
            
            filename_tagging_options = ClientImportOptions.FilenameTaggingOptions()
            
            panel = ClientGUIImport.EditFilenameTaggingOptionPanel( dlg, service_key, filename_tagging_options )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                filename_tagging_options = panel.GetValue()
                
                self._filename_tagging_options.AddDatas( [ ( service_key, filename_tagging_options ) ] )
                
                self._filename_tagging_options.Sort()
                
            
        
    
    def _CheckLocations( self ):
        
        if self._action_successful.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            self._location_successful.Enable()
            
        else:
            
            self._location_successful.Disable()
            
        
        if self._action_redundant.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            self._location_redundant.Enable()
            
        else:
            
            self._location_redundant.Disable()
            
        
        if self._action_deleted.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            self._location_deleted.Enable()
            
        else:
            
            self._location_deleted.Disable()
            
        
        if self._action_failed.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            self._location_failed.Enable()
            
        else:
            
            self._location_failed.Disable()
            
        
    
    def _ConvertFilenameTaggingOptionsToListctrlTuple( self, data ):
        
        ( service_key, filename_tagging_options ) = data
        
        name = HG.client_controller.services_manager.GetName( service_key )
        
        display_tuple = ( name, )
        sort_tuple = ( name, )
        
        return ( display_tuple, sort_tuple )
        
    
    def _DeleteFilenameTaggingOptions( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Delete all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._filename_tagging_options.DeleteSelected()
                
            
        
    
    def _EditFilenameTaggingOptions( self ):
        
        selected_data = self._filename_tagging_options.GetData( only_selected = True )
        
        for data in selected_data:
            
            ( service_key, filename_tagging_options ) = data
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit filename tagging options' ) as dlg:
                
                panel = ClientGUIImport.EditFilenameTaggingOptionPanel( dlg, service_key, filename_tagging_options )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    self._filename_tagging_options.DeleteDatas( ( data, ) )
                    
                    filename_tagging_options = panel.GetValue()
                    
                    self._filename_tagging_options.AddDatas( [ ( service_key, filename_tagging_options ) ] )
                    
                else:
                    
                    break
                    
                
            
        
    
    def _UpdateCheckRegularly( self ):
        
        if self._check_regularly.GetValue():
            
            self._period.Enable()
            
        else:
            
            self._period.Disable()
            
        
    
    def EventCheckRegularly( self, event ):
        
        self._UpdateCheckRegularly()
        
    
    def EventCheckLocations( self, event ):
        
        self._CheckLocations()
        
    
    def EventOK( self, event ):
        
        path = self._path.GetPath()
        
        if path in ( '', None ):
            
            wx.MessageBox( 'You must enter a path to import from!' )
            
            return
            
        
        if not os.path.exists( path ):
            
            wx.MessageBox( 'The path you have entered--"' + path + '"--does not exist! The dialog will not force you to correct it, but this import folder will do no work as long as the location is missing!' )
            
        
        if HC.BASE_DIR.startswith( path ) or HG.client_controller.GetDBDir().startswith( path ):
            
            wx.MessageBox( 'You cannot set an import path that includes your install or database directory!' )
            
            return
            
        
        if self._action_successful.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            path = self._location_successful.GetPath()
            
            if path in ( '', None ):
                
                wx.MessageBox( 'You must enter a path for your successful file move location!' )
                
                return
                
            
            if not os.path.exists( path ):
                
                wx.MessageBox( 'The path you have entered for your successful file move location--"' + path + '"--does not exist! The dialog will not force you to correct it, but you should not let this import folder run until you have corrected or created it!' )
                
            
        
        if self._action_redundant.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            path = self._location_redundant.GetPath()
            
            if path in ( '', None ):
                
                wx.MessageBox( 'You must enter a path for your redundant file move location!' )
                
                return
                
            
            if not os.path.exists( path ):
                
                wx.MessageBox( 'The path you have entered for your redundant file move location--"' + path + '"--does not exist! The dialog will not force you to correct it, but you should not let this import folder run until you have corrected or created it!' )
                
            
        
        if self._action_deleted.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            path = self._location_deleted.GetPath()
            
            if path in ( '', None ):
                
                wx.MessageBox( 'You must enter a path for your deleted file move location!' )
                
                return
                
            
            if not os.path.exists( path ):
                
                wx.MessageBox( 'The path you have entered for your deleted file move location--"' + path + '"--does not exist! The dialog will not force you to correct it, but you should not let this import folder run until you have corrected or created it!' )
                
            
        
        if self._action_failed.GetChoice() == CC.IMPORT_FOLDER_MOVE:
            
            path = self._location_failed.GetPath()
            
            if path in ( '', None ):
                
                wx.MessageBox( 'You must enter a path for your failed file move location!' )
                
                return
                
            
            if not os.path.exists( path ):
                
                wx.MessageBox( 'The path you have entered for your failed file move location--"' + path + '"--does not exist! The dialog will not force you to correct it, but you should not let this import folder run until you have corrected or created it!' )
                
            
        
        self.EndModal( wx.ID_OK )
        
    
    def GetInfo( self ):
        
        name = self._name.GetValue()
        path = HydrusData.ToUnicode( self._path.GetPath() )
        mimes = self._mimes.GetValue()
        file_import_options = self._file_import_options.GetValue()
        tag_import_options = self._tag_import_options.GetValue()
        
        actions = {}
        action_locations = {}
        
        actions[ CC.STATUS_SUCCESSFUL_AND_NEW ] = self._action_successful.GetChoice()
        if actions[ CC.STATUS_SUCCESSFUL_AND_NEW ] == CC.IMPORT_FOLDER_MOVE:
            
            action_locations[ CC.STATUS_SUCCESSFUL_AND_NEW ] = HydrusData.ToUnicode( self._location_successful.GetPath() )
            
        
        actions[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] = self._action_redundant.GetChoice()
        if actions[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] == CC.IMPORT_FOLDER_MOVE:
            
            action_locations[ CC.STATUS_SUCCESSFUL_BUT_REDUNDANT ] = HydrusData.ToUnicode( self._location_redundant.GetPath() )
            
        
        actions[ CC.STATUS_DELETED ] = self._action_deleted.GetChoice()
        if actions[ CC.STATUS_DELETED] == CC.IMPORT_FOLDER_MOVE:
            
            action_locations[ CC.STATUS_DELETED ] = HydrusData.ToUnicode( self._location_deleted.GetPath() )
            
        
        actions[ CC.STATUS_ERROR ] = self._action_failed.GetChoice()
        if actions[ CC.STATUS_ERROR ] == CC.IMPORT_FOLDER_MOVE:
            
            action_locations[ CC.STATUS_ERROR ] = HydrusData.ToUnicode( self._location_failed.GetPath() )
            
        
        period = self._period.GetValue()
        check_regularly = self._check_regularly.GetValue()
        
        paused = self._paused.GetValue()
        
        check_now = self._check_now.GetValue()
        
        show_working_popup = self._show_working_popup.GetValue()
        publish_files_to_popup_button = self._publish_files_to_popup_button.GetValue()
        publish_files_to_page = self._publish_files_to_page.GetValue()
        
        tag_service_keys_to_filename_tagging_options = dict( self._filename_tagging_options.GetData() )
        
        self._import_folder.SetTuple( name, path, mimes, file_import_options, tag_import_options, tag_service_keys_to_filename_tagging_options, actions, action_locations, period, check_regularly, paused, check_now, show_working_popup, publish_files_to_popup_button, publish_files_to_page )
        
        return self._import_folder
        
    
class DialogManagePixivAccount( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage pixiv account' )
        
        self._id = wx.TextCtrl( self )
        self._password = wx.TextCtrl( self )
        
        self._status = ClientGUICommon.BetterStaticText( self )
        
        self._test = wx.Button( self, label = 'test' )
        self._test.Bind( wx.EVT_BUTTON, self.EventTest )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'OK' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'Cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        result = HG.client_controller.Read( 'serialisable_simple', 'pixiv_account' )
        
        if result is None:
            
            result = ( '', '' )
            
        
        ( id, password ) = result
        
        self._id.SetValue( id )
        self._password.SetValue( password )
        
        #
        
        rows = []
        
        rows.append( ( 'id/email: ', self._id ) )
        rows.append( ( 'password: ', self._password ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self, rows )
        
        b_box = wx.BoxSizer( wx.HORIZONTAL )
        b_box.Add( self._ok, CC.FLAGS_VCENTER )
        b_box.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        text = 'In order to search and download from Pixiv, the client needs to log in to it.'
        text += os.linesep
        text += 'Until you put something in here, you will not see the option to download from Pixiv.'
        text += os.linesep
        text += 'You can use a throwaway account if you want--this only needs to log in.'
        
        vbox.Add( ClientGUICommon.BetterStaticText( self, text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( self._status, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._test, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( b_box, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        x = max( x, 240 )
        
        self.SetInitialSize( ( x, y ) )
        
        wx.CallAfter( self._ok.SetFocus )
        
    
    def EventOK( self, event ):
        
        pixiv_id = self._id.GetValue()
        password = self._password.GetValue()
        
        if pixiv_id == '' and password == '':
            
            HG.client_controller.Write( 'serialisable_simple', 'pixiv_account', None )
            
        else:
            
            HG.client_controller.Write( 'serialisable_simple', 'pixiv_account', ( pixiv_id, password ) )
            
        
        self.EndModal( wx.ID_OK )
        
    
    def EventTest( self, event ):
        
        pixiv_id = self._id.GetValue()
        password = self._password.GetValue()
        
        try:
            
            manager = HG.client_controller.network_engine.login_manager
            
            ( result, message ) = manager.TestPixiv( pixiv_id, password )
            
            if result:
                
                self._status.SetLabelText( 'OK!' )
                
                HG.client_controller.CallLaterWXSafe( self._status, 5, self._status.SetLabel, '' )
                
            else:
                
                self._status.SetLabelText( message )
                
            
        except HydrusExceptions.ForbiddenException as e:
            
            HydrusData.ShowException( e )
            
            self._status.SetLabelText( 'Did not work! ' + repr( e ) )
            
        
    
class DialogManageRatings( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, media ):
        
        self._hashes = set()
        
        for m in media: self._hashes.update( m.GetHashes() )
        
        ( remember, position ) = HC.options[ 'rating_dialog_position' ]
        
        if remember and position is not None:
            
            my_position = 'custom'
            
            wx.CallAfter( self.SetPosition, position )
            
        else:
            
            my_position = 'topleft'
            
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'manage ratings for ' + HydrusData.ToHumanInt( len( self._hashes ) ) + ' files', position = my_position )
        
        #
        
        like_services = HG.client_controller.services_manager.GetServices( ( HC.LOCAL_RATING_LIKE, ), randomised = False )
        numerical_services = HG.client_controller.services_manager.GetServices( ( HC.LOCAL_RATING_NUMERICAL, ), randomised = False )
        
        self._panels = []
        
        if len( like_services ) > 0:
            
            self._panels.append( self._LikePanel( self, like_services, media ) )
            
        
        if len( numerical_services ) > 0:
            
            self._panels.append( self._NumericalPanel( self, numerical_services, media ) )
            
        
        self._apply = wx.Button( self, id = wx.ID_OK, label = 'apply' )
        self._apply.Bind( wx.EVT_BUTTON, self.EventOK )
        self._apply.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        buttonbox = wx.BoxSizer( wx.HORIZONTAL )
        
        buttonbox.Add( self._apply, CC.FLAGS_VCENTER )
        buttonbox.Add( self._cancel, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        for panel in self._panels:
            
            vbox.Add( panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        vbox.Add( buttonbox, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        self.SetInitialSize( ( x, y ) )
        
        #
        
        self._my_shortcut_handler = ClientGUIShortcuts.ShortcutsHandler( self, [ 'media' ] )
        
    
    def EventOK( self, event ):
        
        try:
            
            service_keys_to_content_updates = {}
            
            for panel in self._panels:
                
                sub_service_keys_to_content_updates = panel.GetContentUpdates()
                
                service_keys_to_content_updates.update( sub_service_keys_to_content_updates )
                
            
            if len( service_keys_to_content_updates ) > 0:
                
                HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
                
            
            ( remember, position ) = HC.options[ 'rating_dialog_position' ]
            
            current_position = self.GetPosition()
            
            if remember and position != current_position:
                
                HC.options[ 'rating_dialog_position' ] = ( remember, current_position )
                
                HG.client_controller.Write( 'save_options', HC.options )
                
            
        finally:
            
            self.EndModal( wx.ID_OK )
            
        
    
    def ProcessApplicationCommand( self, command ):
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'manage_file_ratings':
                
                self.EventOK( None )
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        return command_processed
        
    
    class _LikePanel( wx.Panel ):
        
        def __init__( self, parent, services, media ):
            
            wx.Panel.__init__( self, parent )
            
            self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_FRAMEBK ) )
            
            self._services = services
            
            self._media = media
            
            self._service_keys_to_controls = {}
            self._service_keys_to_original_ratings_states = {}
            
            rows = []
            
            for service in self._services:
                
                name = service.GetName()
                
                service_key = service.GetServiceKey()
                
                rating_state = ClientRatings.GetLikeStateFromMedia( self._media, service_key )
                
                control = ClientGUICommon.RatingLikeDialog( self, service_key )
                
                control.SetRatingState( rating_state )
                
                self._service_keys_to_controls[ service_key ] = control
                self._service_keys_to_original_ratings_states[ service_key ] = rating_state
                
                rows.append( ( name + ': ', control ) )
                
            
            gridbox = ClientGUICommon.WrapInGrid( self, rows, expand_text = True )
            
            self.SetSizer( gridbox )
            
        
        def GetContentUpdates( self ):
            
            service_keys_to_content_updates = {}
            
            hashes = { hash for hash in itertools.chain.from_iterable( ( media.GetHashes() for media in self._media ) ) }
            
            for ( service_key, control ) in self._service_keys_to_controls.items():
                
                original_rating_state = self._service_keys_to_original_ratings_states[ service_key ]
                
                rating_state = control.GetRatingState()
                
                if rating_state != original_rating_state:
                    
                    if rating_state == ClientRatings.LIKE: rating = 1
                    elif rating_state == ClientRatings.DISLIKE: rating = 0
                    else: rating = None
                    
                    content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_RATINGS, HC.CONTENT_UPDATE_ADD, ( rating, hashes ) )
                    
                    service_keys_to_content_updates[ service_key ] = ( content_update, )
                    
                
            
            return service_keys_to_content_updates
            
        
    
    class _NumericalPanel( wx.Panel ):
        
        def __init__( self, parent, services, media ):
            
            wx.Panel.__init__( self, parent )
            
            self._services = services
            
            self._media = media
            
            self._service_keys_to_controls = {}
            self._service_keys_to_original_ratings_states = {}
            
            rows = []
            
            for service in self._services:
                
                name = service.GetName()
                
                service_key = service.GetServiceKey()
                
                ( rating_state, rating ) = ClientRatings.GetNumericalStateFromMedia( self._media, service_key )
                
                control = ClientGUICommon.RatingNumericalDialog( self, service_key )
                
                if rating_state != ClientRatings.SET:
                    
                    control.SetRatingState( rating_state )
                    
                else:
                    
                    control.SetRating( rating )
                    
                
                self._service_keys_to_controls[ service_key ] = control
                self._service_keys_to_original_ratings_states[ service_key ] = ( rating_state, rating )
                
                rows.append( ( name + ': ', control ) )
                
            
            gridbox = ClientGUICommon.WrapInGrid( self, rows, expand_text = True )
            
            self.SetSizer( gridbox )
            
        
        def GetContentUpdates( self ):
            
            service_keys_to_content_updates = {}
            
            hashes = { hash for hash in itertools.chain.from_iterable( ( media.GetHashes() for media in self._media ) ) }
            
            for ( service_key, control ) in self._service_keys_to_controls.items():
                
                ( original_rating_state, original_rating ) = self._service_keys_to_original_ratings_states[ service_key ]
                
                rating_state = control.GetRatingState()
                
                if rating_state == ClientRatings.NULL:
                    
                    rating = None
                    
                else:
                    
                    rating = control.GetRating()
                    
                
                if rating != original_rating:
                    
                    content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_RATINGS, HC.CONTENT_UPDATE_ADD, ( rating, hashes ) )
                    
                    service_keys_to_content_updates[ service_key ] = ( content_update, )
                    
                
            
            return service_keys_to_content_updates
            
        
    
class DialogManageTagCensorship( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, initial_value = None ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'tag censorship' )
        
        self._tag_services = ClientGUICommon.ListBook( self )
        self._tag_services.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventServiceChanged )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        services = HG.client_controller.services_manager.GetServices( ( HC.COMBINED_TAG, HC.TAG_REPOSITORY, HC.LOCAL_TAG ) )
        
        for service in services:
            
            service_key = service.GetServiceKey()
            name = service.GetName()
            
            page = self._Panel( self._tag_services, service_key, initial_value )
            
            self._tag_services.AddPage( name, service_key, page )
            
        
        self._tag_services.Select( 'all known tags' )
        
        #
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_SMALL_INDENT )
        buttons.Add( self._cancel, CC.FLAGS_SMALL_INDENT )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        intro = "Here you can set which tags or classes of tags you do not want to see. Input something like 'series:' to censor an entire namespace, or ':' for all namespaced tags, and the empty string (just hit enter with no text added) for all unnamespaced tags. You will have to refresh your current queries to see any changes."
        
        st = ClientGUICommon.BetterStaticText( self, intro )
        
        st.SetWrapWidth( 350 )
        
        vbox.Add( st, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._tag_services, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        self.SetInitialSize( ( -1, 480 ) )
        
    
    def _SetSearchFocus( self ):
        
        page = self._tag_services.GetCurrentPage()
        
        if page is not None:
            
            page.SetTagBoxFocus()
            
        
    
    def EventOK( self, event ):
        
        try:
            
            info = [ page.GetInfo() for page in self._tag_services.GetActivePages() if page.HasInfo() ]
            
            HG.client_controller.Write( 'tag_censorship', info )
            
        finally: self.EndModal( wx.ID_OK )
        
    
    def EventServiceChanged( self, event ):
        
        page = self._tag_services.GetCurrentPage()
        
        if page is not None:
            
            wx.CallAfter( page.SetTagBoxFocus )
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, service_key, initial_value = None ):
            
            wx.Panel.__init__( self, parent )
            
            self._service_key = service_key
            
            choice_pairs = [ ( 'blacklist', True ), ( 'whitelist', False ) ]
            
            self._blacklist = ClientGUICommon.RadioBox( self, 'type', choice_pairs )
            
            self._tags = ClientGUIListBoxes.ListBoxTagsCensorship( self )
            
            self._tag_input = wx.TextCtrl( self, style = wx.TE_PROCESS_ENTER )
            self._tag_input.Bind( wx.EVT_KEY_DOWN, self.EventKeyDownTag )
            
            #
            
            ( blacklist, tags ) = HG.client_controller.Read( 'tag_censorship', service_key )
            
            if blacklist: self._blacklist.SetSelection( 0 )
            else: self._blacklist.SetSelection( 1 )
            
            self._tags.AddTags( tags )
            
            if initial_value is not None:
                
                self._tag_input.SetValue( initial_value )
                
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._blacklist, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._tags, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.Add( self._tag_input, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def EventKeyDownTag( self, event ):
            
            ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
            
            if key in ( wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ):
                
                tag = self._tag_input.GetValue()
                
                self._tags.EnterTags( { tag } )
                
                self._tag_input.SetValue( '' )
                
            else: event.Skip()
            
        
        def GetInfo( self ):
            
            blacklist = self._blacklist.GetSelectedClientData()
            
            tags = self._tags.GetClientData()
            
            return ( self._service_key, blacklist, tags )
            
        
        def HasInfo( self ):
            
            ( service_key, blacklist, tags ) = self.GetInfo()
            
            return len( tags ) > 0
            
        
        def SetTagBoxFocus( self ):
            
            self._tag_input.SetFocus()
            
        
    
class DialogManageTagParents( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, tags = None ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'tag parents' )
        
        self._tag_repositories = ClientGUICommon.ListBook( self )
        self._tag_repositories.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventServiceChanged )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        services = HG.client_controller.services_manager.GetServices( ( HC.TAG_REPOSITORY, ) )
        
        for service in services:
            
            if service.HasPermission( HC.CONTENT_TYPE_TAG_PARENTS, HC.PERMISSION_ACTION_PETITION ):
                
                name = service.GetName()
                service_key = service.GetServiceKey()
                
                self._tag_repositories.AddPageArgs( name, service_key, self._Panel, ( self._tag_repositories, service_key, tags ), {} )
                
            
        
        page = self._Panel( self._tag_repositories, CC.LOCAL_TAG_SERVICE_KEY, tags )
        
        name = CC.LOCAL_TAG_SERVICE_KEY
        
        self._tag_repositories.AddPage( name, name, page )
        
        default_tag_repository_key = HC.options[ 'default_tag_repository' ]
        
        self._tag_repositories.Select( default_tag_repository_key )
        
        #
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_SMALL_INDENT )
        buttons.Add( self._cancel, CC.FLAGS_SMALL_INDENT )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._tag_repositories, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        self.SetInitialSize( ( 550, 780 ) )
        
    
    def _SetSearchFocus( self ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        if page is not None:
            
            page.SetTagBoxFocus()
            
        
    
    def EventMenu( self, event ):
        
        action = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetAction( event.GetId() )
        
        if action is not None:
            
            ( command, data ) = action
            
            if command == 'set_search_focus':
                
                self._SetSearchFocus()
                
            else:
                
                event.Skip()
                
            
        
    
    def EventOK( self, event ):
        
        if self._tag_repositories.GetCurrentPage().HasUncommittedPair():
            
            message = 'Are you sure you want to OK? You have an uncommitted pair.'
            
            with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
                
                if dlg.ShowModal() != wx.ID_YES:
                    
                    return
                    
                
            
        
        service_keys_to_content_updates = {}
        
        try:
            
            for page in self._tag_repositories.GetActivePages():
                
                ( service_key, content_updates ) = page.GetContentUpdates()
                
                service_keys_to_content_updates[ service_key ] = content_updates
                
            
            HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
            
        finally:
            
            self.EndModal( wx.ID_OK )
            
        
    
    def EventServiceChanged( self, event ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        if page is not None:
            
            wx.CallAfter( page.SetTagBoxFocus )
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, service_key, tags = None ):
            
            wx.Panel.__init__( self, parent )
            
            self._service_key = service_key
            
            if service_key != CC.LOCAL_TAG_SERVICE_KEY:
                
                self._service = HG.client_controller.services_manager.GetService( service_key )
                
            
            self._pairs_to_reasons = {}
            
            self._original_statuses_to_pairs = {}
            self._current_statuses_to_pairs = {}
            
            self._show_all = wx.CheckBox( self )
            
            listctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
            
            self._tag_parents = ClientGUIListCtrl.BetterListCtrl( listctrl_panel, 'tag_parents', 30, 25, [ ( '', 4 ), ( 'child', 25 ), ( 'parent', -1 ) ], self._ConvertPairToListCtrlTuples, delete_key_callback = self._ListCtrlActivated, activation_callback = self._ListCtrlActivated )
            
            listctrl_panel.SetListCtrl( self._tag_parents )
            
            self._tag_parents.Sort( 2 )
            
            menu_items = []
            
            menu_items.append( ( 'normal', 'from clipboard', 'Load parents from text in your clipboard.', HydrusData.Call( self._ImportFromClipboard, False ) ) )
            menu_items.append( ( 'normal', 'from clipboard (only add pairs--no deletions)', 'Load parents from text in your clipboard.', HydrusData.Call( self._ImportFromClipboard, True ) ) )
            menu_items.append( ( 'normal', 'from .txt file', 'Load parents from a .txt file.', HydrusData.Call( self._ImportFromTXT, False ) ) )
            menu_items.append( ( 'normal', 'from .txt file (only add pairs--no deletions)', 'Load parents from a .txt file.', HydrusData.Call( self._ImportFromTXT, True ) ) )
            
            listctrl_panel.AddMenuButton( 'import', menu_items )
            
            menu_items = []
            
            menu_items.append( ( 'normal', 'to clipboard', 'Save selected parents to your clipboard.', self._ExportToClipboard ) )
            menu_items.append( ( 'normal', 'to .txt file', 'Save selected parents to a .txt file.', self._ExportToTXT ) )
            
            listctrl_panel.AddMenuButton( 'export', menu_items, enabled_only_on_selection = True )
            
            self._children = ClientGUIListBoxes.ListBoxTagsStringsAddRemove( self, self._service_key, show_sibling_text = False )
            self._parents = ClientGUIListBoxes.ListBoxTagsStringsAddRemove( self, self._service_key, show_sibling_text = False )
            
            expand_parents = True
            
            self._child_input = ClientGUIACDropdown.AutoCompleteDropdownTagsWrite( self, self.EnterChildren, expand_parents, CC.LOCAL_FILE_SERVICE_KEY, service_key )
            self._child_input.Disable()
            
            self._parent_input = ClientGUIACDropdown.AutoCompleteDropdownTagsWrite( self, self.EnterParents, expand_parents, CC.LOCAL_FILE_SERVICE_KEY, service_key )
            self._parent_input.Disable()
            
            self._add = wx.Button( self, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAddButton )
            self._add.Disable()
            
            #
            
            #
            
            self._status_st = ClientGUICommon.BetterStaticText( self, u'initialising\u2026' + os.linesep + '.' )
            self._count_st = ClientGUICommon.BetterStaticText( self, '' )
            
            tags_box = wx.BoxSizer( wx.HORIZONTAL )
            
            tags_box.Add( self._children, CC.FLAGS_EXPAND_BOTH_WAYS )
            tags_box.Add( self._parents, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            input_box = wx.BoxSizer( wx.HORIZONTAL )
            
            input_box.Add( self._child_input, CC.FLAGS_EXPAND_BOTH_WAYS )
            input_box.Add( self._parent_input, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._status_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._count_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( ClientGUICommon.WrapInText( self._show_all, self, 'show all pairs' ), CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( listctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.Add( self._add, CC.FLAGS_LONE_BUTTON )
            vbox.Add( tags_box, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.Add( input_box, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
            #
            
            self._tag_parents.Bind( wx.EVT_LIST_ITEM_SELECTED, self.EventItemSelected )
            self._tag_parents.Bind( wx.EVT_LIST_ITEM_DESELECTED, self.EventItemSelected )
            
            self.Bind( ClientGUIListBoxes.EVT_LIST_BOX, self.EventListBoxChanged )
            self._show_all.Bind( wx.EVT_CHECKBOX, self.EventShowAll )
            
            HG.client_controller.CallToThread( self.THREADInitialise, tags, self._service_key )
            
        
        def _AddFlatPairs( self, pairs, add_only = False ):
            
            parents_to_children = HydrusData.BuildKeyToSetDict( ( ( parent, child ) for ( child, parent ) in pairs ) )
            
            for ( parent, children ) in parents_to_children.items():
                
                self._AddPairs( children, parent, add_only = add_only )
                
            
            self._UpdateListCtrlData()
            
            self._SetButtonStatus()
            
        
        def _AddPairs( self, children, parent, add_only = False ):
            
            new_pairs = []
            current_pairs = []
            petitioned_pairs = []
            pending_pairs = []
            
            for child in children:
                
                pair = ( child, parent )
                
                if pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]:
                    
                    if not add_only:
                        
                        pending_pairs.append( pair )
                        
                    
                elif pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]:
                    
                    petitioned_pairs.append( pair )
                    
                elif pair in self._original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ]:
                    
                    if not add_only:
                        
                        current_pairs.append( pair )
                        
                    
                elif self._CanAdd( pair ):
                    
                    new_pairs.append( pair )
                    
                
            
            affected_pairs = []
            
            if len( new_pairs ) > 0:
            
                do_it = True
                
                if self._service_key != CC.LOCAL_TAG_SERVICE_KEY:
                    
                    if self._service.HasPermission( HC.CONTENT_TYPE_TAG_PARENTS, HC.PERMISSION_ACTION_OVERRULE ):
                        
                        reason = 'admin'
                        
                    else:
                        
                        if len( new_pairs ) > 10:
                            
                            pair_strings = 'The many pairs you entered.'
                            
                        else:
                            
                            pair_strings = os.linesep.join( ( child + '->' + parent for ( child, parent ) in new_pairs ) )
                            
                        
                        message = 'Enter a reason for:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'To be added. A janitor will review your petition.'
                        
                        with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                            
                            if dlg.ShowModal() == wx.ID_OK:
                                
                                reason = dlg.GetValue()
                                
                            else: do_it = False
                            
                        
                    
                    if do_it:
                        
                        for pair in new_pairs: self._pairs_to_reasons[ pair ] = reason
                        
                    
                
                if do_it:
                    
                    self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ].update( new_pairs )
                    
                    affected_pairs.extend( new_pairs )
                    
                
            else:
                
                if len( current_pairs ) > 0:
                    
                    do_it = True
                    
                    if self._service_key != CC.LOCAL_TAG_SERVICE_KEY:
                        
                        
                        if len( current_pairs ) > 10:
                            
                            pair_strings = 'The many pairs you entered.'
                            
                        else:
                            
                            pair_strings = os.linesep.join( ( child + '->' + parent for ( child, parent ) in current_pairs ) )
                            
                        
                        if len( current_pairs ) > 1: message = 'The pairs:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'Already exist.'
                        else: message = 'The pair ' + pair_strings + ' already exists.'
                        
                        with ClientGUIDialogs.DialogYesNo( self, message, title = 'Choose what to do.', yes_label = 'petition it', no_label = 'do nothing' ) as dlg:
                            
                            if dlg.ShowModal() == wx.ID_YES:
                                
                                if self._service.HasPermission( HC.CONTENT_TYPE_TAG_PARENTS, HC.PERMISSION_ACTION_OVERRULE ):
                                    
                                    reason = 'admin'
                                    
                                else:
                                    
                                    message = 'Enter a reason for this pair to be removed. A janitor will review your petition.'
                                    
                                    with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                                        
                                        if dlg.ShowModal() == wx.ID_OK:
                                            
                                            reason = dlg.GetValue()
                                            
                                        else: do_it = False
                                        
                                    
                                
                                if do_it:
                                    
                                    for pair in current_pairs: self._pairs_to_reasons[ pair ] = reason
                                    
                                
                                
                            else:
                                
                                do_it = False
                                
                            
                        
                    
                    if do_it:
                        
                        self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ].update( current_pairs )
                        
                        affected_pairs.extend( current_pairs )
                        
                    
                
                if len( pending_pairs ) > 0:
                
                    if len( pending_pairs ) > 10:
                        
                        pair_strings = 'The many pairs you entered.'
                        
                    else:
                        
                        pair_strings = os.linesep.join( ( child + '->' + parent for ( child, parent ) in pending_pairs ) )
                        
                    
                    if len( pending_pairs ) > 1: message = 'The pairs:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'Are pending.'
                    else: message = 'The pair ' + pair_strings + ' is pending.'
                    
                    with ClientGUIDialogs.DialogYesNo( self, message, title = 'Choose what to do.', yes_label = 'rescind the pend', no_label = 'do nothing' ) as dlg:
                        
                        if dlg.ShowModal() == wx.ID_YES:
                            
                            self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ].difference_update( pending_pairs )
                            
                            affected_pairs.extend( pending_pairs )
                            
                        
                    
                
                if len( petitioned_pairs ) > 0:
                
                    if len( petitioned_pairs ) > 10:
                        
                        pair_strings = 'The many pairs you entered.'
                        
                    else:
                        
                        pair_strings = os.linesep.join( ( child + '->' + parent for ( child, parent ) in petitioned_pairs ) )
                        
                    
                    if len( petitioned_pairs ) > 1: message = 'The pairs:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'Are petitioned.'
                    else: message = 'The pair ' + pair_strings + ' is petitioned.'
                    
                    with ClientGUIDialogs.DialogYesNo( self, message, title = 'Choose what to do.', yes_label = 'rescind the petition', no_label = 'do nothing' ) as dlg:
                        
                        if dlg.ShowModal() == wx.ID_YES:
                            
                            self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ].difference_update( petitioned_pairs )
                            
                            affected_pairs.extend( petitioned_pairs )
                            
                        
                    
                
            
            if len( affected_pairs ) > 0:
                
                def in_current( pair ):
                    
                    for status in ( HC.CONTENT_STATUS_CURRENT, HC.CONTENT_STATUS_PENDING, HC.CONTENT_STATUS_PETITIONED ):
                        
                        if pair in self._current_statuses_to_pairs[ status ]:
                            
                            return True
                            
                        
                        return False
                        
                    
                
                affected_pairs = [ ( self._tag_parents.HasData( pair ), in_current( pair ), pair ) for pair in affected_pairs ]
                
                to_add = [ pair for ( exists, current, pair ) in affected_pairs if not exists ]
                to_update = [ pair for ( exists, current, pair ) in affected_pairs if exists and current ]
                to_delete = [ pair for ( exists, current, pair ) in affected_pairs if exists and not current ]
                
                self._tag_parents.AddDatas( to_add )
                self._tag_parents.UpdateDatas( to_update )
                self._tag_parents.DeleteDatas( to_delete )
                
                self._tag_parents.Sort()
                
            
        
        def _CanAdd( self, potential_pair ):
            
            ( potential_child, potential_parent ) = potential_pair
            
            if potential_child == potential_parent: return False
            
            current_pairs = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ].union( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ] ).difference( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ] )
            
            current_children = { child for ( child, parent ) in current_pairs }
            
            # test for loops
            
            if potential_parent in current_children:
                
                simple_children_to_parents = ClientCaches.BuildSimpleChildrenToParents( current_pairs )
                
                if ClientCaches.LoopInSimpleChildrenToParents( simple_children_to_parents, potential_child, potential_parent ):
                    
                    wx.MessageBox( 'Adding ' + potential_child + '->' + potential_parent + ' would create a loop!' )
                    
                    return False
                    
                
            
            return True
            
        
        def _ConvertPairToListCtrlTuples( self, pair ):
            
            ( child, parent ) = pair
            
            if pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]:
                
                status = HC.CONTENT_STATUS_PENDING
                
            elif pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]:
                
                status = HC.CONTENT_STATUS_PETITIONED
                
            elif pair in self._original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ]:
                
                status = HC.CONTENT_STATUS_CURRENT
                
            
            sign = HydrusData.ConvertStatusToPrefix( status )
            
            pretty_status = sign
            
            display_tuple = ( pretty_status, child, parent )
            sort_tuple = ( status, child, parent )
            
            return ( display_tuple, sort_tuple )
            
        
        def _DeserialiseImportString( self, import_string ):
            
            tags = HydrusText.DeserialiseNewlinedTexts( import_string )
            
            if len( tags ) % 2 == 1:
                
                raise Exception( 'Uneven number of tags found!' )
                
            
            pairs = []
            
            for i in range( len( tags ) / 2 ):
                
                pair = ( tags[ 2 * i ], tags[ ( 2 * i ) + 1 ] )
                
                pairs.append( pair )
                
            
            return pairs
            
        
        def _ExportToClipboard( self ):
            
            export_string = self._GetExportString()
            
            HG.client_controller.pub( 'clipboard', 'text', export_string )
            
        
        def _ExportToTXT( self ):
            
            export_string = self._GetExportString()
            
            with wx.FileDialog( self, 'Set the export path.', defaultFile = 'parents.txt', style = wx.FD_SAVE ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    path = dlg.GetPath()
                    
                    with open( path, 'wb' ) as f:
                        
                        f.write( HydrusData.ToByteString( export_string ) )
                        
                    
                
            
        
        def _GetExportString( self ):
            
            tags = []
            
            for ( a, b ) in self._tag_parents.GetData( only_selected = True ):
                
                tags.append( a )
                tags.append( b )
                
            
            export_string = os.linesep.join( tags )
            
            return export_string
            
        
        def _ImportFromClipboard( self, add_only = False ):
            
            import_string = HG.client_controller.GetClipboardText()
            
            pairs = self._DeserialiseImportString( import_string )
            
            self._AddFlatPairs( pairs, add_only )
            
        
        def _ImportFromTXT( self, add_only = False ):
            
            with wx.FileDialog( self, 'Select the file to import.', style = wx.FD_OPEN ) as dlg:
                
                if dlg.ShowModal() != wx.ID_OK:
                    
                    return
                    
                else:
                    
                    path = dlg.GetPath()
                    
                
            
            with open( path, 'rb' ) as f:
                
                import_string = f.read()
                
            
            pairs = self._DeserialiseImportString( import_string )
            
            self._AddFlatPairs( pairs, add_only )
            
        
        def _ListCtrlActivated( self ):
            
            parents_to_children = collections.defaultdict( set )
            
            pairs = self._tag_parents.GetData( only_selected = True )
            
            for ( child, parent ) in pairs:
                
                parents_to_children[ parent ].add( child )
                
            
            if len( parents_to_children ) > 0:
                
                for ( parent, children ) in parents_to_children.items():
                    
                    self._AddPairs( children, parent )
                    
                
            
        
        def _SetButtonStatus( self ):
            
            if len( self._children.GetTags() ) == 0 or len( self._parents.GetTags() ) == 0:
                
                self._add.Disable()
                
            else:
                
                self._add.Enable()
                
            
        
        def _UpdateListCtrlData( self ):
            
            children = self._children.GetTags()
            parents = self._parents.GetTags()
            
            pertinent_tags = children.union( parents )
            
            self._tag_parents.DeleteDatas( self._tag_parents.GetData() )
            
            all_pairs = set()
            
            show_all = self._show_all.GetValue()
            
            for ( status, pairs ) in self._current_statuses_to_pairs.items():
                
                if status == HC.CONTENT_STATUS_DELETED:
                    
                    continue
                    
                
                if len( pertinent_tags ) == 0:
                    
                    if status == HC.CONTENT_STATUS_CURRENT and not show_all:
                        
                        continue
                        
                    
                    # show all pending/petitioned
                    
                    all_pairs.update( pairs )
                    
                else:
                    
                    # show all appropriate
                    
                    for pair in pairs:
                        
                        ( a, b ) = pair
                        
                        if a in pertinent_tags or b in pertinent_tags or show_all:
                            
                            all_pairs.add( pair )
                            
                        
                    
                
            
            self._tag_parents.AddDatas( all_pairs )
            
            self._tag_parents.Sort()
            
        
        def EnterChildren( self, tags ):
            
            if len( tags ) > 0:
                
                self._parents.RemoveTags( tags )
                
                self._children.EnterTags( tags )
                
                self._UpdateListCtrlData()
                
                self._SetButtonStatus()
                
            
        
        def EnterParents( self, tags ):
            
            if len( tags ) > 0:
                
                self._children.RemoveTags( tags )
                
                self._parents.EnterTags( tags )
                
                self._UpdateListCtrlData()
                
                self._SetButtonStatus()
                
            
        
        def EventAddButton( self, event ):
            
            children = self._children.GetTags()
            parents = self._parents.GetTags()
            
            for parent in parents:
                
                self._AddPairs( children, parent )
                
            
            self._children.SetTags( [] )
            self._parents.SetTags( [] )
            
            self._UpdateListCtrlData()
            
            self._SetButtonStatus()
            
        
        def EventItemSelected( self, event ):
            
            self._SetButtonStatus()
            
            event.Skip()
            
        
        def EventListBoxChanged( self, event ):
            
            self._UpdateListCtrlData()
            
        
        def EventShowAll( self, event ):
            
            self._UpdateListCtrlData()
            
        
        def GetContentUpdates( self ):
            
            # we make it manually here because of the mass pending tags done (but not undone on a rescind) on a pending pair!
            # we don't want to send a pend and then rescind it, cause that will spam a thousand bad tags and not undo it
            
            content_updates = []
            
            if self._service_key == CC.LOCAL_TAG_SERVICE_KEY:
                
                for pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]: content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_ADD, pair ) )
                for pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]: content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_DELETE, pair ) )
                
            else:
                
                current_pending = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]
                original_pending = self._original_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]
                
                current_petitioned = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]
                original_petitioned = self._original_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]
                
                new_pends = current_pending.difference( original_pending )
                rescinded_pends = original_pending.difference( current_pending )
                
                new_petitions = current_petitioned.difference( original_petitioned )
                rescinded_petitions = original_petitioned.difference( current_petitioned )
                
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_PEND, ( pair, self._pairs_to_reasons[ pair ] ) ) for pair in new_pends ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_RESCIND_PEND, pair ) for pair in rescinded_pends ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_PETITION, ( pair, self._pairs_to_reasons[ pair ] ) ) for pair in new_petitions ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_PARENTS, HC.CONTENT_UPDATE_RESCIND_PETITION, pair ) for pair in rescinded_petitions ) )
                
            
            return ( self._service_key, content_updates )
            
        
        def HasUncommittedPair( self ):
            
            return len( self._children.GetTags() ) > 0 and len( self._parents.GetTags() ) > 0
            
        
        def SetTagBoxFocus( self ):
            
            if len( self._children.GetTags() ) == 0: self._child_input.SetFocus()
            else: self._parent_input.SetFocus()
            
        
        def THREADInitialise( self, tags, service_key ):
            
            def wx_code( original_statuses_to_pairs, current_statuses_to_pairs ):
                
                if not self:
                    
                    return
                    
                
                self._original_statuses_to_pairs = original_statuses_to_pairs
                self._current_statuses_to_pairs = current_statuses_to_pairs
                
                self._status_st.SetLabelText( 'Files with a tag on the left will also be given the tag on the right.' + os.linesep + 'As an experiment, this panel will only display the \'current\' pairs for those tags entered below.' )
                self._count_st.SetLabelText( 'Starting with ' + HydrusData.ToHumanInt( len( original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ] ) ) + ' pairs.' )
                
                self._child_input.Enable()
                self._parent_input.Enable()
                
                if tags is None:
                    
                    self._UpdateListCtrlData()
                    
                else:
                    
                    self.EnterChildren( tags )
                    
                
            
            original_statuses_to_pairs = HG.client_controller.Read( 'tag_parents', service_key )
            
            current_statuses_to_pairs = collections.defaultdict( set )
            
            current_statuses_to_pairs.update( { key : set( value ) for ( key, value ) in original_statuses_to_pairs.items() } )
            
            wx.CallAfter( wx_code, original_statuses_to_pairs, current_statuses_to_pairs )
            
        
    
class DialogManageTagSiblings( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent, tags = None ):
        
        ClientGUIDialogs.Dialog.__init__( self, parent, 'tag siblings' )
        
        self._tag_repositories = ClientGUICommon.ListBook( self )
        self._tag_repositories.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.EventServiceChanged )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        self._cancel = wx.Button( self, id = wx.ID_CANCEL, label = 'cancel' )
        self._cancel.SetForegroundColour( ( 128, 0, 0 ) )
        
        #
        
        page = self._Panel( self._tag_repositories, CC.LOCAL_TAG_SERVICE_KEY, tags )
        
        name = CC.LOCAL_TAG_SERVICE_KEY
        
        self._tag_repositories.AddPage( name, name, page )
        
        services = HG.client_controller.services_manager.GetServices( ( HC.TAG_REPOSITORY, ) )
        
        for service in services:
            
            if service.HasPermission( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.PERMISSION_ACTION_PETITION ):
                
                name = service.GetName()
                service_key = service.GetServiceKey()
                
                self._tag_repositories.AddPageArgs( name, service_key, self._Panel, ( self._tag_repositories, service_key, tags ), {} )
                
            
        
        default_tag_repository_key = HC.options[ 'default_tag_repository' ]
        
        self._tag_repositories.Select( default_tag_repository_key )
        
        #
        
        buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        buttons.Add( self._ok, CC.FLAGS_SMALL_INDENT )
        buttons.Add( self._cancel, CC.FLAGS_SMALL_INDENT )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._tag_repositories, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
        self.SetInitialSize( ( 850, 780 ) )
        
    
    def _SetSearchFocus( self ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        if page is not None:
            
            page.SetTagBoxFocus()
            
        
    
    def EventMenu( self, event ):
        
        action = ClientCaches.MENU_EVENT_ID_TO_ACTION_CACHE.GetAction( event.GetId() )
        
        if action is not None:
            
            ( command, data ) = action
            
            if command == 'set_search_focus':
                
                self._SetSearchFocus()
                
            else:
                
                event.Skip()
                
            
        
    
    def EventOK( self, event ):
        
        if self._tag_repositories.GetCurrentPage().HasUncommittedPair():
            
            message = 'Are you sure you want to OK? You have an uncommitted pair.'
            
            with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
                
                if dlg.ShowModal() != wx.ID_YES:
                    
                    return
                    
                
            
        
        service_keys_to_content_updates = {}
        
        try:
            
            for page in self._tag_repositories.GetActivePages():
                
                ( service_key, content_updates ) = page.GetContentUpdates()
                
                service_keys_to_content_updates[ service_key ] = content_updates
                
            
            HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
            
        finally: self.EndModal( wx.ID_OK )
        
    
    def EventServiceChanged( self, event ):
        
        page = self._tag_repositories.GetCurrentPage()
        
        if page is not None:
            
            wx.CallAfter( page.SetTagBoxFocus )
            
        
    
    class _Panel( wx.Panel ):
        
        def __init__( self, parent, service_key, tags = None ):
            
            wx.Panel.__init__( self, parent )
            
            self._service_key = service_key
            
            if self._service_key != CC.LOCAL_TAG_SERVICE_KEY:
                
                self._service = HG.client_controller.services_manager.GetService( service_key )
                
            
            self._original_statuses_to_pairs = {}
            self._current_statuses_to_pairs = {}
            
            self._pairs_to_reasons = {}
            
            self._current_new = None
            
            self._show_all = wx.CheckBox( self )
            
            listctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
            
            self._tag_siblings = ClientGUIListCtrl.BetterListCtrl( listctrl_panel, 'tag_siblings', 30, 40, [ ( '', 4 ), ( 'old', 25 ), ( 'new', 25 ), ( 'note', -1 ) ], self._ConvertPairToListCtrlTuples, delete_key_callback = self._ListCtrlActivated, activation_callback = self._ListCtrlActivated )
            
            listctrl_panel.SetListCtrl( self._tag_siblings )
            
            self._tag_siblings.Sort( 2 )
            
            menu_items = []
            
            menu_items.append( ( 'normal', 'from clipboard', 'Load siblings from text in your clipboard.', HydrusData.Call( self._ImportFromClipboard, False ) ) )
            menu_items.append( ( 'normal', 'from clipboard (only add pairs--no deletions)', 'Load siblings from text in your clipboard.', HydrusData.Call( self._ImportFromClipboard, True ) ) )
            menu_items.append( ( 'normal', 'from .txt file', 'Load siblings from a .txt file.', HydrusData.Call( self._ImportFromTXT, False ) ) )
            menu_items.append( ( 'normal', 'from .txt file (only add pairs--no deletions)', 'Load siblings from a .txt file.', HydrusData.Call( self._ImportFromTXT, True ) ) )
            
            listctrl_panel.AddMenuButton( 'import', menu_items )
            
            menu_items = []
            
            menu_items.append( ( 'normal', 'to clipboard', 'Save selected siblings to your clipboard.', self._ExportToClipboard ) )
            menu_items.append( ( 'normal', 'to .txt file', 'Save selected siblings to a .txt file.', self._ExportToTXT ) )
            
            listctrl_panel.AddMenuButton( 'export', menu_items, enabled_only_on_selection = True )
            
            self._old_siblings = ClientGUIListBoxes.ListBoxTagsStringsAddRemove( self, self._service_key, show_sibling_text = False )
            self._new_sibling = ClientGUICommon.BetterStaticText( self )
            
            expand_parents = False
            
            self._old_input = ClientGUIACDropdown.AutoCompleteDropdownTagsWrite( self, self.EnterOlds, expand_parents, CC.LOCAL_FILE_SERVICE_KEY, service_key )
            self._old_input.Disable()
            
            self._new_input = ClientGUIACDropdown.AutoCompleteDropdownTagsWrite( self, self.SetNew, expand_parents, CC.LOCAL_FILE_SERVICE_KEY, service_key )
            self._new_input.Disable()
            
            self._add = wx.Button( self, label = 'add' )
            self._add.Bind( wx.EVT_BUTTON, self.EventAddButton )
            self._add.Disable()
            
            #
            
            self._status_st = ClientGUICommon.BetterStaticText( self, u'initialising\u2026' )
            self._count_st = ClientGUICommon.BetterStaticText( self, '' )
            
            new_sibling_box = wx.BoxSizer( wx.VERTICAL )
            
            new_sibling_box.Add( ( 10, 10 ), CC.FLAGS_EXPAND_BOTH_WAYS )
            new_sibling_box.Add( self._new_sibling, CC.FLAGS_EXPAND_PERPENDICULAR )
            new_sibling_box.Add( ( 10, 10 ), CC.FLAGS_EXPAND_BOTH_WAYS )
            
            text_box = wx.BoxSizer( wx.HORIZONTAL )
            
            text_box.Add( self._old_siblings, CC.FLAGS_EXPAND_BOTH_WAYS )
            text_box.Add( new_sibling_box, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
            
            input_box = wx.BoxSizer( wx.HORIZONTAL )
            
            input_box.Add( self._old_input, CC.FLAGS_EXPAND_BOTH_WAYS )
            input_box.Add( self._new_input, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._status_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._count_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( ClientGUICommon.WrapInText( self._show_all, self, 'show all pairs' ), CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( listctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
            vbox.Add( self._add, CC.FLAGS_LONE_BUTTON )
            vbox.Add( text_box, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.Add( input_box, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
            #
            
            self._tag_siblings.Bind( wx.EVT_LIST_ITEM_SELECTED, self.EventItemSelected )
            self._tag_siblings.Bind( wx.EVT_LIST_ITEM_DESELECTED, self.EventItemSelected )
            
            self._show_all.Bind( wx.EVT_CHECKBOX, self.EventShowAll )
            self.Bind( ClientGUIListBoxes.EVT_LIST_BOX, self.EventListBoxChanged )
            
            HG.client_controller.CallToThread( self.THREADInitialise, tags, self._service_key )
            
        
        def _AddFlatPairs( self, pairs, add_only = False ):
            
            news_to_olds = HydrusData.BuildKeyToSetDict( ( ( new, old ) for ( old, new ) in pairs ) )
            
            for ( new, olds ) in news_to_olds.items():
                
                self._AutoPetitionConflicts( olds, new )
                
                self._AddPairs( olds, new, add_only = add_only )
                
            
            self._UpdateListCtrlData()
            
            self._SetButtonStatus()
            
        
        def _AddPairs( self, olds, new, add_only = False, remove_only = False, default_reason = None ):
            
            new_pairs = []
            current_pairs = []
            petitioned_pairs = []
            pending_pairs = []
            
            for old in olds:
                
                pair = ( old, new )
                
                if pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]:
                    
                    if not add_only:
                        
                        pending_pairs.append( pair )
                        
                    
                elif pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]:
                    
                    if not remove_only:
                        
                        petitioned_pairs.append( pair )
                        
                    
                elif pair in self._original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ]:
                    
                    if not add_only:
                        
                        current_pairs.append( pair )
                        
                    
                elif not remove_only and self._CanAdd( pair ):
                    
                    new_pairs.append( pair )
                    
                
            
            if len( new_pairs ) > 0:
                
                do_it = True
                
                if self._service_key != CC.LOCAL_TAG_SERVICE_KEY:
                    
                    if default_reason is not None:
                        
                        reason = default_reason
                        
                    elif self._service.HasPermission( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.PERMISSION_ACTION_OVERRULE ):
                        
                        reason = 'admin'
                        
                    else:
                        
                        if len( new_pairs ) > 10:
                            
                            pair_strings = 'The many pairs you entered.'
                            
                        else:
                            
                            pair_strings = os.linesep.join( ( old + '->' + new for ( old, new ) in new_pairs ) )
                            
                        
                        message = 'Enter a reason for:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'To be added. A janitor will review your petition.'
                        
                        with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                            
                            if dlg.ShowModal() == wx.ID_OK:
                                
                                reason = dlg.GetValue()
                                
                            else:
                                
                                do_it = False
                                
                            
                        
                    
                    if do_it:
                        
                        for pair in new_pairs: self._pairs_to_reasons[ pair ] = reason
                        
                    
                
                if do_it:
                    
                    self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ].update( new_pairs )
                    
                
            else:
                
                if len( current_pairs ) > 0:
                    
                    do_it = True
                    
                    if self._service_key != CC.LOCAL_TAG_SERVICE_KEY:
                        
                        if default_reason is not None:
                            
                            reason = default_reason
                            
                        elif self._service.HasPermission( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.PERMISSION_ACTION_OVERRULE ):
                            
                            reason = 'admin'
                            
                        else:
                            
                            if len( pending_pairs ) > 10:
                                
                                pair_strings = 'The many pairs you entered.'
                                
                            else:
                                
                                pair_strings = os.linesep.join( ( old + '->' + new for ( old, new ) in pending_pairs ) )
                                
                            
                            message = 'Enter a reason for:'
                            message += os.linesep * 2
                            message += pair_strings
                            message += os.linesep * 2
                            message += 'to be removed. You will see the delete as soon as you upload, but a janitor will review your petition to decide if all users should receive it as well.'
                            
                            with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                                
                                if dlg.ShowModal() == wx.ID_OK:
                                    
                                    reason = dlg.GetValue()
                                    
                                else:
                                    
                                    do_it = False
                                    
                                
                            
                        
                        if do_it:
                            
                            for pair in current_pairs:
                                
                                self._pairs_to_reasons[ pair ] = reason
                                
                            
                        
                    
                    self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ].update( current_pairs )
                    
                
                if len( pending_pairs ) > 0:
                    
                    if len( pending_pairs ) > 10:
                        
                        pair_strings = 'The many pairs you entered.'
                        
                    else:
                        
                        pair_strings = os.linesep.join( ( old + '->' + new for ( old, new ) in pending_pairs ) )
                        
                    
                    if len( pending_pairs ) > 1:
                        
                        message = 'The pairs:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'Are pending.'
                        
                    else:
                        
                        message = 'The pair ' + pair_strings + ' is pending.'
                        
                    
                    with ClientGUIDialogs.DialogYesNo( self, message, title = 'Choose what to do.', yes_label = 'rescind the pend', no_label = 'do nothing' ) as dlg:
                        
                        if dlg.ShowModal() == wx.ID_YES:
                            
                            self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ].difference_update( pending_pairs )
                            
                        
                    
                
                if len( petitioned_pairs ) > 0:
                
                    if len( petitioned_pairs ) > 10:
                        
                        pair_strings = 'The many pairs you entered.'
                        
                    else:
                        
                        pair_strings = ', '.join( ( old + '->' + new for ( old, new ) in petitioned_pairs ) )
                        
                    
                    if len( petitioned_pairs ) > 1: message = 'The pairs:' + os.linesep * 2 + pair_strings + os.linesep * 2 + 'Are petitioned.'
                    else: message = 'The pair ' + pair_strings + ' is petitioned.'
                    
                    with ClientGUIDialogs.DialogYesNo( self, message, title = 'Choose what to do.', yes_label = 'rescind the petition', no_label = 'do nothing' ) as dlg:
                        
                        if dlg.ShowModal() == wx.ID_YES:
                            
                            self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ].difference_update( petitioned_pairs )
                            
                        
                    
                
            
        
        def _AutoPetitionConflicts( self, olds, new ):
            
            current_pairs = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ].union( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ] ).difference( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ] )
            
            olds_to_news = dict( current_pairs )
            
            current_olds = { current_old for ( current_old, current_new ) in current_pairs }
            
            for old in olds:
                
                if old in current_olds:
                    
                    conflicting_new = olds_to_news[ old ]
                    
                    if conflicting_new != new:
                        
                        self._AddPairs( [ old ], conflicting_new, remove_only = True, default_reason = 'AUTO-PETITION TO REASSIGN TO: ' + new )
                        
                    
                
            
        
        def _CanAdd( self, potential_pair ):
            
            ( potential_old, potential_new ) = potential_pair
            
            current_pairs = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ].union( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ] ).difference( self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ] )
            
            current_olds = { old for ( old, new ) in current_pairs }
            
            # test for ambiguity
            
            if potential_old in current_olds:
                
                wx.MessageBox( 'There already is a relationship set for the tag ' + potential_old + '.' )
                
                return False
                
            
            # test for loops
            
            if potential_new in current_olds:
                
                d = dict( current_pairs )
                
                next_new = potential_new
                
                while next_new in d:
                    
                    next_new = d[ next_new ]
                    
                    if next_new == potential_old:
                        
                        wx.MessageBox( 'Adding ' + potential_old + '->' + potential_new + ' would create a loop!' )
                        
                        return False
                        
                    
                
            
            return True
            
        
        def _ConvertPairToListCtrlTuples( self, pair ):
            
            ( old, new ) = pair
            
            if pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]:
                
                status = HC.CONTENT_STATUS_PENDING
                
            elif pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]:
                
                status = HC.CONTENT_STATUS_PETITIONED
                
            elif pair in self._original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ]:
                
                status = HC.CONTENT_STATUS_CURRENT
                
            
            sign = HydrusData.ConvertStatusToPrefix( status )
            
            pretty_status = sign
            
            existing_olds = self._old_siblings.GetTags()
            
            note = ''
            
            if old in existing_olds:
                
                if status == HC.CONTENT_STATUS_PENDING:
                    
                    note = 'CONFLICT: Will be rescinded on add.'
                    
                elif status == HC.CONTENT_STATUS_CURRENT:
                    
                    note = 'CONFLICT: Will be petitioned/deleted on add.'
                    
                
            
            display_tuple = ( pretty_status, old, new, note )
            sort_tuple = ( status, old, new, note )
            
            return ( display_tuple, sort_tuple )
            
        
        def _DeserialiseImportString( self, import_string ):
            
            tags = HydrusText.DeserialiseNewlinedTexts( import_string )
            
            if len( tags ) % 2 == 1:
                
                raise Exception( 'Uneven number of tags found!' )
                
            
            pairs = []
            
            for i in range( len( tags ) / 2 ):
                
                pair = ( tags[ 2 * i ], tags[ ( 2 * i ) + 1 ] )
                
                pairs.append( pair )
                
            
            return pairs
            
        
        def _ExportToClipboard( self ):
            
            export_string = self._GetExportString()
            
            HG.client_controller.pub( 'clipboard', 'text', export_string )
            
        
        def _ExportToTXT( self ):
            
            export_string = self._GetExportString()
            
            with wx.FileDialog( self, 'Set the export path.', defaultFile = 'parents.txt', style = wx.FD_SAVE ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    path = dlg.GetPath()
                    
                    with open( path, 'wb' ) as f:
                        
                        f.write( HydrusData.ToByteString( export_string ) )
                        
                    
                
            
        
        def _GetExportString( self ):
            
            tags = []
            
            for ( a, b ) in self._tag_siblings.GetData( only_selected = True ):
                
                tags.append( a )
                tags.append( b )
                
            
            export_string = os.linesep.join( tags )
            
            return export_string
            
        
        def _ImportFromClipboard( self, add_only = False ):
            
            import_string = HG.client_controller.GetClipboardText()
            
            pairs = self._DeserialiseImportString( import_string )
            
            self._AddFlatPairs( pairs, add_only )
            
        
        def _ImportFromTXT( self, add_only = False ):
            
            with wx.FileDialog( self, 'Select the file to import.', style = wx.FD_OPEN ) as dlg:
                
                if dlg.ShowModal() != wx.ID_OK:
                    
                    return
                    
                else:
                    
                    path = dlg.GetPath()
                    
                
            
            with open( path, 'rb' ) as f:
                
                import_string = f.read()
                
            
            pairs = self._DeserialiseImportString( import_string )
            
            self._AddFlatPairs( pairs, add_only )
            
        
        def _ListCtrlActivated( self ):
            
            news_to_olds = collections.defaultdict( set )
            
            pairs = self._tag_siblings.GetData( only_selected = True )
            
            for ( old, new ) in pairs:
                
                news_to_olds[ new ].add( old )
                
            
            if len( news_to_olds ) > 0:
                
                for ( new, olds ) in news_to_olds.items():
                    
                    self._AddPairs( olds, new )
                    
                
            
            self._UpdateListCtrlData()
            
        
        def _SetButtonStatus( self ):
            
            if self._current_new is None or len( self._old_siblings.GetTags() ) == 0:
                
                self._add.Disable()
                
            else:
                
                self._add.Enable()
                
            
        
        def _UpdateListCtrlData( self ):
            
            olds = self._old_siblings.GetTags()
            
            pertinent_tags = set( olds )
            
            if self._current_new is not None:
                
                pertinent_tags.add( self._current_new )
                
            
            self._tag_siblings.DeleteDatas( self._tag_siblings.GetData() )
            
            all_pairs = set()
            
            show_all = self._show_all.GetValue()
            
            for ( status, pairs ) in self._current_statuses_to_pairs.items():
                
                if status == HC.CONTENT_STATUS_DELETED:
                    
                    continue
                    
                
                if len( pertinent_tags ) == 0:
                    
                    if status == HC.CONTENT_STATUS_CURRENT and not show_all:
                        
                        continue
                        
                    
                    # show all pending/petitioned
                    
                    all_pairs.update( pairs )
                    
                else:
                    
                    # show all appropriate
                    
                    for pair in pairs:
                        
                        ( a, b ) = pair
                        
                        if a in pertinent_tags or b in pertinent_tags or show_all:
                            
                            all_pairs.add( pair )
                            
                        
                    
                
            
            self._tag_siblings.AddDatas( all_pairs )
            
            self._tag_siblings.Sort()
            
        
        def EnterOlds( self, olds ):
            
            if self._current_new in olds:
                
                self.SetNew( set() )
                
            
            self._old_siblings.EnterTags( olds )
            
            self._UpdateListCtrlData()
            
            self._SetButtonStatus()
            
        
        def EventAddButton( self, event ):
            
            if self._current_new is not None and len( self._old_siblings.GetTags() ) > 0:
                
                olds = self._old_siblings.GetTags()
                
                self._AutoPetitionConflicts( olds, self._current_new )
                
                self._AddPairs( olds, self._current_new )
                
                self._old_siblings.SetTags( set() )
                self.SetNew( set() )
                
                self._UpdateListCtrlData()
                
                self._SetButtonStatus()
                
            
        
        def EventItemSelected( self, event ):
            
            self._SetButtonStatus()
            
            event.Skip()
            
        
        def EventListBoxChanged( self, event ):
            
            self._UpdateListCtrlData()
            
        
        def EventShowAll( self, event ):
            
            self._UpdateListCtrlData()
            
        
        def GetContentUpdates( self ):
            
            # we make it manually here because of the mass pending tags done (but not undone on a rescind) on a pending pair!
            # we don't want to send a pend and then rescind it, cause that will spam a thousand bad tags and not undo it
            
            # actually, we don't do this for siblings, but we do for parents, and let's have them be the same
            
            content_updates = []
            
            if self._service_key == CC.LOCAL_TAG_SERVICE_KEY:
                
                for pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]:
                    
                    content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_ADD, pair ) )
                    
                
                for pair in self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]:
                    
                    content_updates.append( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_DELETE, pair ) )
                    
                
            else:
                
                current_pending = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]
                original_pending = self._original_statuses_to_pairs[ HC.CONTENT_STATUS_PENDING ]
                
                current_petitioned = self._current_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]
                original_petitioned = self._original_statuses_to_pairs[ HC.CONTENT_STATUS_PETITIONED ]
                
                new_pends = current_pending.difference( original_pending )
                rescinded_pends = original_pending.difference( current_pending )
                
                new_petitions = current_petitioned.difference( original_petitioned )
                rescinded_petitions = original_petitioned.difference( current_petitioned )
                
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_PEND, ( pair, self._pairs_to_reasons[ pair ] ) ) for pair in new_pends ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_RESCIND_PEND, pair ) for pair in rescinded_pends ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_PETITION, ( pair, self._pairs_to_reasons[ pair ] ) ) for pair in new_petitions ) )
                content_updates.extend( ( HydrusData.ContentUpdate( HC.CONTENT_TYPE_TAG_SIBLINGS, HC.CONTENT_UPDATE_RESCIND_PETITION, pair ) for pair in rescinded_petitions ) )
                
            
            return ( self._service_key, content_updates )
            
        
        def HasUncommittedPair( self ):
            
            return len( self._old_siblings.GetTags() ) > 0 and self._current_new is not None
            
        
        def SetNew( self, new_tags ):
            
            if len( new_tags ) == 0:
                
                self._new_sibling.SetLabelText( '' )
                
                self._current_new = None
                
            else:
                
                new = list( new_tags )[0]
                
                self._old_siblings.RemoveTags( { new } )
                
                self._new_sibling.SetLabelText( new )
                
                self._current_new = new
                
            
            self._UpdateListCtrlData()
            
            self._SetButtonStatus()
            
        
        def SetTagBoxFocus( self ):
            
            if len( self._old_siblings.GetTags() ) == 0:
                
                self._old_input.SetFocus()
                
            else:
                
                self._new_input.SetFocus()
                
            
        
        def THREADInitialise( self, tags, service_key ):
            
            def wx_code( original_statuses_to_pairs, current_statuses_to_pairs ):
                
                if not self:
                    
                    return
                    
                
                self._original_statuses_to_pairs = original_statuses_to_pairs
                self._current_statuses_to_pairs = current_statuses_to_pairs
                
                self._status_st.SetLabelText( 'Tags on the left will be replaced by those on the right.' )
                self._count_st.SetLabelText( 'Starting with ' + HydrusData.ToHumanInt( len( original_statuses_to_pairs[ HC.CONTENT_STATUS_CURRENT ] ) ) + ' pairs.' )
                
                self._old_input.Enable()
                self._new_input.Enable()
                
                if tags is None:
                    
                    self._UpdateListCtrlData()
                    
                else:
                    
                    self.EnterOlds( tags )
                    
                
            
            original_statuses_to_pairs = HG.client_controller.Read( 'tag_siblings', service_key )
            
            current_statuses_to_pairs = collections.defaultdict( set )
            
            current_statuses_to_pairs.update( { key : set( value ) for ( key, value ) in original_statuses_to_pairs.items() } )
            
            wx.CallAfter( wx_code, original_statuses_to_pairs, current_statuses_to_pairs )
            
        
    
class DialogManageUPnP( ClientGUIDialogs.Dialog ):
    
    def __init__( self, parent ):
        
        title = 'manage local upnp'
        
        ClientGUIDialogs.Dialog.__init__( self, parent, title )
        
        self._hidden_cancel = wx.Button( self, id = wx.ID_CANCEL, size = ( 0, 0 ) )
        
        self._status_st = ClientGUICommon.BetterStaticText( self )
        
        self._mappings_list_ctrl = ClientGUIListCtrl.SaneListCtrl( self, 480, [ ( 'description', -1 ), ( 'internal ip', 100 ), ( 'internal port', 80 ), ( 'external ip', 100 ), ( 'external port', 80 ), ( 'protocol', 80 ), ( 'lease', 80 ) ], delete_key_callback = self.RemoveMappings, activation_callback = self.EditMappings )
        
        self._add_custom = wx.Button( self, label = 'add custom mapping' )
        self._add_custom.Bind( wx.EVT_BUTTON, self.EventAddCustomMapping )
        
        self._edit = wx.Button( self, label = 'edit mapping' )
        self._edit.Bind( wx.EVT_BUTTON, self.EventEditMapping )
        
        self._remove = wx.Button( self, label = 'remove mapping' )
        self._remove.Bind( wx.EVT_BUTTON, self.EventRemoveMapping )
        
        self._ok = wx.Button( self, id = wx.ID_OK, label = 'ok' )
        self._ok.Bind( wx.EVT_BUTTON, self.EventOK )
        self._ok.SetForegroundColour( ( 0, 128, 0 ) )
        
        #
        
        edit_buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        edit_buttons.Add( self._add_custom, CC.FLAGS_VCENTER )
        edit_buttons.Add( self._edit, CC.FLAGS_VCENTER )
        edit_buttons.Add( self._remove, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._status_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._mappings_list_ctrl, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( edit_buttons, CC.FLAGS_BUTTON_SIZER )
        vbox.Add( self._ok, CC.FLAGS_LONE_BUTTON )
        
        self.SetSizer( vbox )
        
        ( x, y ) = self.GetEffectiveMinSize()
        
        x = max( x, 760 )
        
        self.SetInitialSize( ( x, y ) )
        
        #
        
        self._RefreshMappings()
        
    
    def _RefreshMappings( self ):
        
        def THREADdo_it():
            
            def wx_code( mappings ):
                
                if not self:
                    
                    return
                    
                
                self._mappings = mappings
                
                for mapping in self._mappings:
                    
                    self._mappings_list_ctrl.Append( mapping, mapping )
                    
                
                self._status_st.SetLabelText( '' )
                
            
            try:
                
                mappings = HydrusNATPunch.GetUPnPMappings()
                
            except Exception as e:
                
                HydrusData.ShowException( e )
                
                wx.CallAfter( wx.MessageBox, 'Could not load mappings:' + os.linesep * 2 + str( e ) )
                
                return
                
            
            wx.CallAfter( wx_code, mappings )
            
        
        self._status_st.SetLabelText( 'Refreshing mappings--please wait...' )
        
        self._mappings_list_ctrl.DeleteAllItems()
        
        HG.client_controller.CallToThread( THREADdo_it )
        
    
    def EditMappings( self ):
        
        do_refresh = False
        
        for index in self._mappings_list_ctrl.GetAllSelected():
            
            ( description, internal_ip, internal_port, external_ip, external_port, protocol, duration ) = self._mappings_list_ctrl.GetClientData( index )
            
            with ClientGUIDialogs.DialogInputUPnPMapping( self, external_port, protocol, internal_port, description, duration ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    ( external_port, protocol, internal_port, description, duration ) = dlg.GetInfo()
                    
                    HydrusNATPunch.RemoveUPnPMapping( external_port, protocol )
                    
                    internal_client = HydrusNATPunch.GetLocalIP()
                    
                    HydrusNATPunch.AddUPnPMapping( internal_client, internal_port, external_port, protocol, description, duration = duration )
                    
                    do_refresh = True
                    
                
            
        
        if do_refresh:
            
            self._RefreshMappings()
            
        
    
    def EventAddCustomMapping( self, event ):
        
        do_refresh = False
        
        external_port = HC.DEFAULT_SERVICE_PORT
        protocol = 'TCP'
        internal_port = HC.DEFAULT_SERVICE_PORT
        description = 'hydrus service'
        duration = 0
        
        with ClientGUIDialogs.DialogInputUPnPMapping( self, external_port, protocol, internal_port, description, duration ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                ( external_port, protocol, internal_port, description, duration ) = dlg.GetInfo()
                
                for ( existing_description, existing_internal_ip, existing_internal_port, existing_external_ip, existing_external_port, existing_protocol, existing_lease ) in self._mappings:
                    
                    if external_port == existing_external_port and protocol == existing_protocol:
                        
                        wx.MessageBox( 'That external port already exists!' )
                        
                        return
                        
                    
                
                internal_client = HydrusNATPunch.GetLocalIP()
                
                HydrusNATPunch.AddUPnPMapping( internal_client, internal_port, external_port, protocol, description, duration = duration )
                
                do_refresh = True
                
            
        
        if do_refresh:
            
            self._RefreshMappings()
            
        
    
    def EventEditMapping( self, event ):
        
        self.EditMappings()
        
    
    def EventOK( self, event ):
        
        self.EndModal( wx.ID_OK )
        
    
    def EventRemoveMapping( self, event ):
        
        self.RemoveMappings()
        
    
    def RemoveMappings( self ):
        
        do_refresh = False
        
        for index in self._mappings_list_ctrl.GetAllSelected():
            
            ( description, internal_ip, internal_port, external_ip, external_port, protocol, duration ) = self._mappings_list_ctrl.GetClientData( index )
            
            HydrusNATPunch.RemoveUPnPMapping( external_port, protocol )
            
            do_refresh = True
            
        
        if do_refresh:
            
            self._RefreshMappings()
            
        
