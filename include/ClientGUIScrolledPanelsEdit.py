import ClientConstants as CC
import ClientData
import ClientDefaults
import ClientDownloading
import ClientDuplicates
import ClientImporting
import ClientGUICommon
import ClientGUIControls
import ClientGUIDialogs
import ClientGUIImport
import ClientGUIListBoxes
import ClientGUIListCtrl
import ClientGUIParsing
import ClientGUIScrolledPanels
import ClientGUIFileSeedCache
import ClientGUIGallerySeedLog
import ClientGUISerialisable
import ClientGUIShortcuts
import ClientGUITime
import ClientGUITopLevelWindows
import ClientImportFileSeeds
import ClientImportOptions
import ClientNetworkingContexts
import ClientNetworkingDomain
import ClientParsing
import ClientPaths
import ClientSerialisable
import ClientTags
import collections
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals as HG
import HydrusNetwork
import HydrusSerialisable
import HydrusTags
import HydrusText
import os
import wx

class EditAccountTypePanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, service_type, account_type ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        ( self._account_type_key, title, permissions, bandwidth_rules ) = account_type.ToTuple()
        
        self._title = wx.TextCtrl( self )
        
        permission_choices = self._GeneratePermissionChoices( service_type )
        
        self._permission_controls = []
        
        self._permissions_panel = ClientGUICommon.StaticBox( self, 'permissions' )
        
        gridbox_rows = []
        
        for ( content_type, action_rows ) in permission_choices:
            
            choice_control = ClientGUICommon.BetterChoice( self._permissions_panel )
            
            for ( label, action ) in action_rows:
                
                choice_control.Append( label, ( content_type, action ) )
                
            
            if content_type in permissions:
                
                selection_row = ( content_type, permissions[ content_type ] )
                
            else:
                
                selection_row = ( content_type, None )
                
            
            try:
                
                choice_control.SelectClientData( selection_row )
                
            except:
                
                choice_control.SelectClientData( ( content_type, None ) )
                
            
            self._permission_controls.append( choice_control )
            
            gridbox_label = HC.content_type_string_lookup[ content_type ]
            
            gridbox_rows.append( ( gridbox_label, choice_control ) )
            
        
        gridbox = ClientGUICommon.WrapInGrid( self._permissions_panel, gridbox_rows )
        
        self._bandwidth_rules_control = ClientGUIControls.BandwidthRulesCtrl( self, bandwidth_rules )
        
        #
        
        self._title.SetValue( title )
        
        #
        
        t_hbox = ClientGUICommon.WrapInText( self._title, self, 'title: ' )
        
        self._permissions_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( t_hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( self._permissions_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._bandwidth_rules_control, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def _GeneratePermissionChoices( self, service_type ):
        
        possible_permissions = HydrusNetwork.GetPossiblePermissions( service_type )
        
        permission_choices = []
        
        for ( content_type, possible_actions ) in possible_permissions:
            
            choices = []
            
            for action in possible_actions:
                
                choices.append( ( HC.permission_pair_string_lookup[ ( content_type, action ) ], action ) )
                
            
            permission_choices.append( ( content_type, choices ) )
            
        
        return permission_choices
        
    
    def GetValue( self ):
        
        title = self._title.GetValue()
        
        permissions = {}
        
        for permission_control in self._permission_controls:
            
            ( content_type, action ) = permission_control.GetChoice()
            
            if action is not None:
                
                permissions[ content_type ] = action
                
            
        
        bandwidth_rules = self._bandwidth_rules_control.GetValue()
        
        return HydrusNetwork.AccountType.GenerateAccountTypeFromParameters( self._account_type_key, title, permissions, bandwidth_rules )
        
    
class EditBandwidthRulesPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, bandwidth_rules, summary = '' ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._bandwidth_rules_ctrl = ClientGUIControls.BandwidthRulesCtrl( self, bandwidth_rules )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        if summary != '':
            
            st = ClientGUICommon.BetterStaticText( self, summary )
            
            st.SetWrapWidth( 250 )
            
            vbox.Add( st, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        vbox.Add( self._bandwidth_rules_ctrl, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        return self._bandwidth_rules_ctrl.GetValue()
        
    
class EditChooseMultiple( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, choice_tuples ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._checkboxes = wx.CheckListBox( self )
        
        self._checkboxes.SetMinSize( ( 320, 420 ) )
        
        for ( i, ( label, data, selected ) ) in enumerate( choice_tuples ):
            
            self._checkboxes.Append( label, data )
            
            if selected:
                
                self._checkboxes.Check( i )
                
            
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._checkboxes, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        datas = []
        
        for index in self._checkboxes.GetCheckedItems():
            
            datas.append( self._checkboxes.GetClientData( index ) )
            
        
        return datas
        
    
class EditCookiePanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, name, value, domain, path, expires ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._name = wx.TextCtrl( self )
        self._value = wx.TextCtrl( self )
        self._domain = wx.TextCtrl( self )
        self._path = wx.TextCtrl( self )
        
        expires_panel = ClientGUICommon.StaticBox( self, 'expires' )
        
        self._expires_st = ClientGUICommon.BetterStaticText( expires_panel )
        self._expires_st_utc = ClientGUICommon.BetterStaticText( expires_panel )
        self._expires_time_delta = ClientGUITime.TimeDeltaButton( expires_panel, min = 1200, days = True, hours = True, minutes = True )
        
        #
        
        self._name.SetValue( name )
        self._value.SetValue( value )
        self._domain.SetValue( domain )
        self._path.SetValue( path )
        
        self._expires = expires
        
        self._expires_time_delta.SetValue( 30 * 86400 )
        
        #
        
        rows = []
        
        rows.append( ( 'Actual expires as UTC Timestamp: ', self._expires_st_utc ) )
        rows.append( ( 'Set expires as a delta from now: ', self._expires_time_delta ) )
        
        gridbox = ClientGUICommon.WrapInGrid( expires_panel, rows )
        
        expires_panel.Add( self._expires_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        expires_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        rows = []
        
        rows.append( ( 'name: ', self._name ) )
        rows.append( ( 'value: ', self._value ) )
        rows.append( ( 'domain: ', self._domain ) )
        rows.append( ( 'path: ', self._path ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self, rows )
        
        vbox.Add( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( expires_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        #
        
        self._UpdateExpiresText()
        
        self._expires_time_delta.Bind( ClientGUITime.EVT_TIME_DELTA, self.EventTimeDelta )
        
    
    def _UpdateExpiresText( self ):
        
        self._expires_st.SetLabelText( HydrusData.ConvertTimestampToPrettyExpires( self._expires ) )
        self._expires_st_utc.SetLabelText( str( self._expires ) )
        
    
    def EventTimeDelta( self, event ):
        
        time_delta = self._expires_time_delta.GetValue()
        
        expires = HydrusData.GetNow() + time_delta
        
        self._expires = expires
        
        self._UpdateExpiresText()
        
    
    def GetValue( self ):
        
        name = self._name.GetValue()
        value = self._value.GetValue()
        domain = self._domain.GetValue()
        path = self._path.GetValue()
        expires = self._expires
        
        return ( name, value, domain, path, expires )
        
    
class EditDefaultTagImportOptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, url_matches, parsers, url_match_keys_to_parser_keys, file_post_default_tag_import_options, watchable_default_tag_import_options, url_match_keys_to_tag_import_options ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._url_matches = url_matches
        self._parsers = parsers
        self._url_match_keys_to_parser_keys = url_match_keys_to_parser_keys
        self._parser_keys_to_parsers = { parser.GetParserKey() : parser for parser in self._parsers }
        
        self._url_match_keys_to_tag_import_options = dict( url_match_keys_to_tag_import_options )
        
        #
        
        self._file_post_default_tag_import_options_button = ClientGUIImport.TagImportOptionsButton( self, [], file_post_default_tag_import_options )
        self._watchable_default_tag_import_options_button = ClientGUIImport.TagImportOptionsButton( self, [], watchable_default_tag_import_options )
        
        self._list_ctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
        
        self._list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._list_ctrl_panel, 'default_tag_import_options', 15, 36, [ ( 'url class', -1 ), ( 'url type', 12 ), ( 'defaults set?', 15 ) ], self._ConvertDataToListCtrlTuples, delete_key_callback = self._Clear, activation_callback = self._Edit )
        
        self._list_ctrl_panel.SetListCtrl( self._list_ctrl )
        
        self._list_ctrl_panel.AddButton( 'edit', self._Edit, enabled_only_on_selection = True )
        self._list_ctrl_panel.AddButton( 'clear', self._Clear, enabled_only_on_selection = True )
        
        #
        
        eligible_url_matches = [ url_match for url_match in url_matches if url_match.GetURLType() in ( HC.URL_TYPE_POST, HC.URL_TYPE_WATCHABLE ) and url_match.GetMatchKey() in self._url_match_keys_to_parser_keys ]
        
        self._list_ctrl.AddDatas( eligible_url_matches )
        
        self._list_ctrl.Sort( 1 )
        
        #
        
        rows = []
        
        rows.append( ( 'default for file posts: ', self._file_post_default_tag_import_options_button ) )
        rows.append( ( 'default for watchable urls: ', self._watchable_default_tag_import_options_button ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self, rows )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._list_ctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def _ConvertDataToListCtrlTuples( self, url_match ):
        
        url_match_key = url_match.GetMatchKey()
        
        name = url_match.GetName()
        url_type = url_match.GetURLType()
        defaults_set = url_match_key in self._url_match_keys_to_tag_import_options
        
        pretty_name = name
        pretty_url_type = HC.url_type_string_lookup[ url_type ]
        
        if defaults_set:
            
            pretty_default_set = 'yes'
            
        else:
            
            pretty_default_set = ''
            
        
        display_tuple = ( pretty_name, pretty_url_type, pretty_default_set )
        sort_tuple = ( name, pretty_url_type, defaults_set )
        
        return ( display_tuple, sort_tuple )
        
    
    def _Clear( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Clear default tag import options for all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                url_matches_to_clear = self._list_ctrl.GetData( only_selected = True )
                
                for url_match in url_matches_to_clear:
                    
                    url_match_key = url_match.GetMatchKey()
                    
                    if url_match_key in self._url_match_keys_to_tag_import_options:
                        
                        del self._url_match_keys_to_tag_import_options[ url_match_key ]
                        
                    
                
                self._list_ctrl.UpdateDatas( url_matches_to_clear )
                
            
        
    
    def _Edit( self ):
        
        url_matches_to_edit = self._list_ctrl.GetData( only_selected = True )
        
        for url_match in url_matches_to_edit:
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit tag import options' ) as dlg:
                
                ( namespaces, tag_import_options ) = self._GetNamespacesAndDefaultTagImportOptions( url_match )
                
                panel = EditTagImportOptionsPanel( dlg, namespaces, tag_import_options )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    url_match_key = url_match.GetMatchKey()
                    
                    tag_import_options = panel.GetValue()
                    
                    self._url_match_keys_to_tag_import_options[ url_match_key ] = tag_import_options
                    
                else:
                    
                    break
                    
                
            
        
        self._list_ctrl.UpdateDatas( url_matches_to_edit )
        
    
    def _GetNamespacesAndDefaultTagImportOptions( self, url_match ):
        
        parser_key = self._url_match_keys_to_parser_keys[ url_match.GetMatchKey() ]
        
        parser = self._parser_keys_to_parsers[ parser_key ]
        
        namespaces = parser.GetNamespaces()
        
        url_match_key = url_match.GetMatchKey()
        
        if url_match_key in self._url_match_keys_to_tag_import_options:
            
            tag_import_options = self._url_match_keys_to_tag_import_options[ url_match_key ]
            
        else:
            
            url_types_to_guidance_tag_import_options = {}
            
            url_types_to_guidance_tag_import_options[ HC.URL_TYPE_POST ] = self._file_post_default_tag_import_options_button.GetValue()
            url_types_to_guidance_tag_import_options[ HC.URL_TYPE_WATCHABLE ] = self._watchable_default_tag_import_options_button.GetValue()
            
            namespaces = parser.GetNamespaces()
            
            tag_import_options = ClientNetworkingDomain.DeriveDefaultTagImportOptionsForURLMatch( namespaces, url_types_to_guidance_tag_import_options, url_match )
            
        
        return ( namespaces, tag_import_options )
        
    
    def GetValue( self ):
        
        file_post_default_tag_import_options = self._file_post_default_tag_import_options_button.GetValue()
        watchable_default_tag_import_options = self._watchable_default_tag_import_options_button.GetValue()
        
        return ( file_post_default_tag_import_options, watchable_default_tag_import_options, self._url_match_keys_to_tag_import_options )
        
    
class EditDomainManagerInfoPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, url_matches, network_contexts_to_custom_header_dicts ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._notebook = wx.Notebook( self )
        
        self._url_matches_panel = EditURLMatchesPanel( self._notebook, url_matches )
        self._network_contexts_to_custom_header_dicts_panel = EditNetworkContextCustomHeadersPanel( self._notebook, network_contexts_to_custom_header_dicts )
        
        self._notebook.AddPage( self._url_matches_panel, 'url classes', select = True )
        self._notebook.AddPage( self._network_contexts_to_custom_header_dicts_panel, 'custom headers', select = False )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._notebook, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        url_matches = self._url_matches_panel.GetValue()
        network_contexts_to_custom_header_dicts = self._network_contexts_to_custom_header_dicts_panel.GetValue()
        
        return ( url_matches, network_contexts_to_custom_header_dicts )
        
    
class EditDuplicateActionOptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, duplicate_action, duplicate_action_options, for_custom_action = False ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._duplicate_action = duplicate_action
        
        #
        
        tag_services_panel = ClientGUICommon.StaticBox( self, 'tag services' )
        
        self._tag_service_actions = ClientGUIListCtrl.SaneListCtrl( tag_services_panel, 120, [ ( 'service name', 120 ), ( 'action', 240 ), ( 'tags merged', -1 ) ], delete_key_callback = self._DeleteTag, activation_callback = self._EditTag )
        
        self._tag_service_actions.SetMinSize( ( 560, 120 ) )
        
        add_tag_button = ClientGUICommon.BetterButton( tag_services_panel, 'add', self._AddTag )
        edit_tag_button = ClientGUICommon.BetterButton( tag_services_panel, 'edit', self._EditTag )
        delete_tag_button = ClientGUICommon.BetterButton( tag_services_panel, 'delete', self._DeleteTag )
        
        #
        
        rating_services_panel = ClientGUICommon.StaticBox( self, 'rating services' )
        
        self._rating_service_actions = ClientGUIListCtrl.SaneListCtrl( rating_services_panel, 120, [ ( 'service name', -1 ), ( 'action', 240 ) ], delete_key_callback = self._DeleteRating, activation_callback = self._EditRating )
        
        self._rating_service_actions.SetMinSize( ( 380, 120 ) )
        
        add_rating_button = ClientGUICommon.BetterButton( rating_services_panel, 'add', self._AddRating )
        
        if self._duplicate_action == HC.DUPLICATE_BETTER: # because there is only one valid action otherwise
            
            edit_rating_button = ClientGUICommon.BetterButton( rating_services_panel, 'edit', self._EditRating )
            
        
        delete_rating_button = ClientGUICommon.BetterButton( rating_services_panel, 'delete', self._DeleteRating )
        
        #
        
        self._delete_second_file = wx.CheckBox( self )
        self._sync_archive = wx.CheckBox( self )
        self._delete_both_files = wx.CheckBox( self )
        
        self._delete_both_files.SetToolTip( 'This is only enabled on custom actions.' )
        
        self._sync_urls_action = ClientGUICommon.BetterChoice( self )
        
        self._sync_urls_action.Append( 'sync nothing', None )
        
        if self._duplicate_action == HC.DUPLICATE_BETTER:
            
            self._sync_urls_action.Append( HC.content_merge_string_lookup[ HC.CONTENT_MERGE_ACTION_COPY ], HC.CONTENT_MERGE_ACTION_COPY )
            
        
        self._sync_urls_action.Append( HC.content_merge_string_lookup[ HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ], HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE )
        
        #
        
        ( tag_service_options, rating_service_options, delete_second_file, sync_archive, delete_both_files, sync_urls_action ) = duplicate_action_options.ToTuple()
        
        services_manager = HG.client_controller.services_manager
        
        for ( service_key, action, tag_filter ) in tag_service_options:
            
            if services_manager.ServiceExists( service_key ):
                
                sort_tuple = ( service_key, action, tag_filter )
                
                display_tuple = self._GetTagDisplayTuple( sort_tuple )
                
                self._tag_service_actions.Append( display_tuple, sort_tuple )
                
            
        
        for ( service_key, action ) in rating_service_options:
            
            if services_manager.ServiceExists( service_key ):
                
                sort_tuple = ( service_key, action )
                
                display_tuple = self._GetRatingDisplayTuple( sort_tuple )
                
                self._rating_service_actions.Append( display_tuple, sort_tuple )
                
            
        
        self._delete_second_file.SetValue( delete_second_file )
        self._sync_archive.SetValue( sync_archive )
        self._delete_both_files.SetValue( delete_both_files )
        
        #
        
        if not for_custom_action:
            
            self._delete_both_files.Disable()
            
        
        if self._duplicate_action in ( HC.DUPLICATE_ALTERNATE, HC.DUPLICATE_NOT_DUPLICATE ) and not for_custom_action:
            
            self._sync_archive.Disable()
            self._sync_urls_action.Disable()
            
            self._sync_urls_action.SelectClientData( None )
            
        else:
            
            self._sync_urls_action.SelectClientData( sync_urls_action )
            
        
        if self._duplicate_action != HC.DUPLICATE_BETTER:
            
            self._delete_second_file.Disable()
            
        
        #
        
        button_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        button_hbox.Add( add_tag_button, CC.FLAGS_VCENTER )
        button_hbox.Add( edit_tag_button, CC.FLAGS_VCENTER )
        button_hbox.Add( delete_tag_button, CC.FLAGS_VCENTER )
        
        tag_services_panel.Add( self._tag_service_actions, CC.FLAGS_EXPAND_BOTH_WAYS )
        tag_services_panel.Add( button_hbox, CC.FLAGS_BUTTON_SIZER )
        
        #
        
        button_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        button_hbox.Add( add_rating_button, CC.FLAGS_VCENTER )
        if self._duplicate_action == HC.DUPLICATE_BETTER:
            
            button_hbox.Add( edit_rating_button, CC.FLAGS_VCENTER )
            
        button_hbox.Add( delete_rating_button, CC.FLAGS_VCENTER )
        
        rating_services_panel.Add( self._rating_service_actions, CC.FLAGS_EXPAND_BOTH_WAYS )
        rating_services_panel.Add( button_hbox, CC.FLAGS_BUTTON_SIZER )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( tag_services_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( rating_services_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        rows = []
        
        rows.append( ( 'delete worse file: ', self._delete_second_file ) )
        rows.append( ( 'delete both files: ', self._delete_both_files ) )
        rows.append( ( 'if one file is archived, archive the other as well: ', self._sync_archive ) )
        rows.append( ( 'sync known urls?: ', self._sync_urls_action ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self, rows )
        
        vbox.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def _AddRating( self ):
        
        existing_service_keys = set()
        
        for ( service_key, action ) in self._rating_service_actions.GetClientData():
            
            existing_service_keys.add( service_key )
            
        
        services_manager = HG.client_controller.services_manager
        
        choice_tuples = []
        
        for service in services_manager.GetServices( [ HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ] ):
            
            service_key = service.GetServiceKey()
            
            if service_key not in existing_service_keys:
                
                name = service.GetName()
                
                choice_tuples.append( ( name, service_key ) )
                
            
        
        if len( choice_tuples ) == 0:
            
            wx.MessageBox( 'You have no more tag or rating services to add! Try editing the existing ones instead!' )
            
        else:
            
            with ClientGUIDialogs.DialogSelectFromList( self, 'select service', choice_tuples ) as dlg_1:
                
                if dlg_1.ShowModal() == wx.ID_OK:
                    
                    service_key = dlg_1.GetChoice()
                    
                    if self._duplicate_action == HC.DUPLICATE_BETTER:
                        
                        service = services_manager.GetService( service_key )
                        
                        if service.GetServiceType() == HC.TAG_REPOSITORY:
                            
                            possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                            
                        else:
                            
                            possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_MOVE, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                            
                        
                        choice_tuples = [ ( HC.content_merge_string_lookup[ action ], action ) for action in possible_actions ]
                        
                        with ClientGUIDialogs.DialogSelectFromList( self, 'select action', choice_tuples ) as dlg_2:
                            
                            if dlg_2.ShowModal() == wx.ID_OK:
                                
                                action = dlg_2.GetChoice()
                                
                            else:
                                
                                return
                                
                            
                        
                    else:
                        
                        action = HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE
                        
                    
                    sort_tuple = ( service_key, action )
                    
                    display_tuple = self._GetRatingDisplayTuple( sort_tuple )
                    
                    self._rating_service_actions.Append( display_tuple, sort_tuple )
                    
                
            
        
    
    def _AddTag( self ):
        
        existing_service_keys = set()
        
        for ( service_key, action, tag_filter ) in self._tag_service_actions.GetClientData():
            
            existing_service_keys.add( service_key )
            
        
        services_manager = HG.client_controller.services_manager
        
        choice_tuples = []
        
        for service in services_manager.GetServices( [ HC.LOCAL_TAG, HC.TAG_REPOSITORY ] ):
            
            service_key = service.GetServiceKey()
            
            if service_key not in existing_service_keys:
                
                name = service.GetName()
                
                choice_tuples.append( ( name, service_key ) )
                
            
        
        if len( choice_tuples ) == 0:
            
            wx.MessageBox( 'You have no more tag or rating services to add! Try editing the existing ones instead!' )
            
        else:
            
            with ClientGUIDialogs.DialogSelectFromList( self, 'select service', choice_tuples ) as dlg_1:
                
                if dlg_1.ShowModal() == wx.ID_OK:
                    
                    service_key = dlg_1.GetChoice()
                    
                    if self._duplicate_action == HC.DUPLICATE_BETTER:
                        
                        service = services_manager.GetService( service_key )
                        
                        if service.GetServiceType() == HC.TAG_REPOSITORY:
                            
                            possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                            
                        else:
                            
                            possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_MOVE, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                            
                        
                        choice_tuples = [ ( HC.content_merge_string_lookup[ action ], action ) for action in possible_actions ]
                        
                        with ClientGUIDialogs.DialogSelectFromList( self, 'select action', choice_tuples ) as dlg_2:
                            
                            if dlg_2.ShowModal() == wx.ID_OK:
                                
                                action = dlg_2.GetChoice()
                                
                            else:
                                
                                return
                                
                            
                        
                    else:
                        
                        action = HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE
                        
                    
                    tag_filter = ClientTags.TagFilter()
                    
                    with ClientGUITopLevelWindows.DialogEdit( self, 'edit which tags will be merged' ) as dlg_3:
                        
                        panel = EditTagFilterPanel( dlg_3, tag_filter )
                        
                        dlg_3.SetPanel( panel )
                        
                        if dlg_3.ShowModal() == wx.ID_OK:
                            
                            tag_filter = panel.GetValue()
                            
                            sort_tuple = ( service_key, action, tag_filter )
                            
                            display_tuple = self._GetTagDisplayTuple( sort_tuple )
                            
                            self._tag_service_actions.Append( display_tuple, sort_tuple )
                            
                        
                    
                
            
        
    
    def _DeleteRating( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._rating_service_actions.RemoveAllSelected()
                
            
        
    
    def _DeleteTag( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._tag_service_actions.RemoveAllSelected()
                
            
        
    
    def _EditRating( self ):
        
        all_selected = self._rating_service_actions.GetAllSelected()
        
        for index in all_selected:
            
            ( service_key, action ) = self._rating_service_actions.GetClientData( index )
            
            if self._duplicate_action == HC.DUPLICATE_BETTER:
                
                possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_MOVE, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                
                choice_tuples = [ ( HC.content_merge_string_lookup[ action ], action ) for action in possible_actions ]
                
                with ClientGUIDialogs.DialogSelectFromList( self, 'select action', choice_tuples ) as dlg_2:
                    
                    if dlg_2.ShowModal() == wx.ID_OK:
                        
                        action = dlg_2.GetChoice()
                        
                    else:
                        
                        break
                        
                    
                
            else: # This shouldn't get fired because the edit button is hidden, but w/e
                
                action = HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE
                
            
            sort_tuple = ( service_key, action )
            
            display_tuple = self._GetRatingDisplayTuple( sort_tuple )
            
            self._rating_service_actions.UpdateRow( index, display_tuple, sort_tuple )
            
        
    
    def _EditTag( self ):
        
        all_selected = self._tag_service_actions.GetAllSelected()
        
        for index in all_selected:
            
            ( service_key, action, tag_filter ) = self._tag_service_actions.GetClientData( index )
            
            if self._duplicate_action == HC.DUPLICATE_BETTER:
                
                possible_actions = [ HC.CONTENT_MERGE_ACTION_COPY, HC.CONTENT_MERGE_ACTION_MOVE, HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE ]
                
                choice_tuples = [ ( HC.content_merge_string_lookup[ action ], action ) for action in possible_actions ]
                
                with ClientGUIDialogs.DialogSelectFromList( self, 'select action', choice_tuples ) as dlg_2:
                    
                    if dlg_2.ShowModal() == wx.ID_OK:
                        
                        action = dlg_2.GetChoice()
                        
                    else:
                        
                        break
                        
                    
                
            else:
                
                action = HC.CONTENT_MERGE_ACTION_TWO_WAY_MERGE
                
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit which tags will be merged' ) as dlg_3:
                
                panel = EditTagFilterPanel( dlg_3, tag_filter )
                
                dlg_3.SetPanel( panel )
                
                if dlg_3.ShowModal() == wx.ID_OK:
                    
                    tag_filter = panel.GetValue()
                    
                    sort_tuple = ( service_key, action, tag_filter )
                    
                    display_tuple = self._GetTagDisplayTuple( sort_tuple )
                    
                    self._tag_service_actions.UpdateRow( index, display_tuple, sort_tuple )
                    
                else:
                    
                    break
                    
                
            
        
    
    def _GetRatingDisplayTuple( self, sort_tuple ):
        
        ( service_key, action ) = sort_tuple
        
        services_manager = HG.client_controller.services_manager
        
        service = services_manager.GetService( service_key )
        
        name = service.GetName()
        
        pretty_action = HC.content_merge_string_lookup[ action ]
        
        return ( name, pretty_action )
        
    
    def _GetTagDisplayTuple( self, sort_tuple ):
        
        ( service_key, action, tag_filter ) = sort_tuple
        
        services_manager = HG.client_controller.services_manager
        
        service = services_manager.GetService( service_key )
        
        name = service.GetName()
        
        pretty_action = HC.content_merge_string_lookup[ action ]
        
        pretty_tag_filter = tag_filter.ToPermittedString()
        
        return ( name, pretty_action, pretty_tag_filter )
        
    
    def GetValue( self ):
        
        tag_service_actions = self._tag_service_actions.GetClientData()
        rating_service_actions = self._rating_service_actions.GetClientData()
        delete_second_file = self._delete_second_file.GetValue()
        sync_archive = self._sync_archive.GetValue()
        delete_both_files = self._delete_both_files.GetValue()
        sync_urls_action = self._sync_urls_action.GetChoice()
        
        duplicate_action_options = ClientDuplicates.DuplicateActionOptions( tag_service_actions, rating_service_actions, delete_second_file, sync_archive, delete_both_files, sync_urls_action )
        
        return duplicate_action_options
        
    
class EditFileImportOptions( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, file_import_options ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        help_button = ClientGUICommon.BetterBitmapButton( self, CC.GlobalBMPs.help, self._ShowHelp )
        
        help_hbox = ClientGUICommon.WrapInText( help_button, self, 'help for this panel -->', wx.Colour( 0, 0, 255 ) )
        
        #
        
        pre_import_panel = ClientGUICommon.StaticBox( self, 'pre-import checks' )
        
        self._exclude_deleted = wx.CheckBox( pre_import_panel )
        
        self._allow_decompression_bombs = wx.CheckBox( pre_import_panel )
        
        self._min_size = ClientGUIControls.NoneableBytesControl( pre_import_panel )
        self._min_size.SetValue( 5 * 1024 )
        
        self._max_size = ClientGUIControls.NoneableBytesControl( pre_import_panel )
        self._max_size.SetValue( 100 * 1024 * 1024 )
        
        self._max_gif_size = ClientGUIControls.NoneableBytesControl( pre_import_panel )
        self._max_gif_size.SetValue( 32 * 1024 * 1024 )
        
        self._min_resolution = ClientGUICommon.NoneableSpinCtrl( pre_import_panel, num_dimensions = 2 )
        self._min_resolution.SetValue( ( 50, 50 ) )
        
        self._max_resolution = ClientGUICommon.NoneableSpinCtrl( pre_import_panel, num_dimensions = 2 )
        self._max_resolution.SetValue( ( 8192, 8192 ) )
        
        #
        
        post_import_panel = ClientGUICommon.StaticBox( self, 'post-import actions' )
        
        self._auto_archive = wx.CheckBox( post_import_panel )
        
        #
        
        presentation_panel = ClientGUICommon.StaticBox( self, 'presentation options' )
        
        self._present_new_files = wx.CheckBox( presentation_panel )
        self._present_already_in_inbox_files = wx.CheckBox( presentation_panel )
        self._present_already_in_archive_files = wx.CheckBox( presentation_panel )
        
        #
        
        ( exclude_deleted, allow_decompression_bombs, min_size, max_size, max_gif_size, min_resolution, max_resolution ) = file_import_options.GetPreImportOptions()
        
        self._exclude_deleted.SetValue( exclude_deleted )
        self._allow_decompression_bombs.SetValue( allow_decompression_bombs )
        self._min_size.SetValue( min_size )
        self._max_size.SetValue( max_size )
        self._max_gif_size.SetValue( max_gif_size )
        self._min_resolution.SetValue( min_resolution )
        self._max_resolution.SetValue( max_resolution )
        
        #
        
        automatic_archive = file_import_options.GetPostImportOptions()
        
        self._auto_archive.SetValue( automatic_archive )
        
        #
        
        ( present_new_files, present_already_in_inbox_files, present_already_in_archive_files ) = file_import_options.GetPresentationOptions()
        
        self._present_new_files.SetValue( present_new_files )
        self._present_already_in_inbox_files.SetValue( present_already_in_inbox_files )
        self._present_already_in_archive_files.SetValue( present_already_in_archive_files )
        
        #
        
        rows = []
        
        rows.append( ( 'exclude previously deleted files: ', self._exclude_deleted ) )
        rows.append( ( 'allow decompression bombs: ', self._allow_decompression_bombs ) )
        rows.append( ( 'minimum filesize: ', self._min_size ) )
        rows.append( ( 'maximum filesize: ', self._max_size ) )
        rows.append( ( 'maximum gif filesize: ', self._max_gif_size ) )
        rows.append( ( 'minimum resolution: ', self._min_resolution ) )
        rows.append( ( 'maximum resolution: ', self._max_resolution ) )
        
        gridbox = ClientGUICommon.WrapInGrid( pre_import_panel, rows )
        
        pre_import_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'archive all imports: ', self._auto_archive ) )
        
        gridbox = ClientGUICommon.WrapInGrid( post_import_panel, rows )
        
        post_import_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'present new files', self._present_new_files ) )
        rows.append( ( 'present \'already in db\' files in inbox', self._present_already_in_inbox_files ) )
        rows.append( ( 'present \'already in db\' files in archive', self._present_already_in_archive_files ) )
        
        gridbox = ClientGUICommon.WrapInGrid( presentation_panel, rows )
        
        presentation_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( help_hbox, CC.FLAGS_BUTTON_SIZER )
        vbox.Add( pre_import_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( post_import_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( presentation_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def _ShowHelp( self ):
        
        help_message = '''-exclude previously deleted files-

If this is set and an incoming file has already been seen and deleted before by this client, the import will be abandoned. This is useful to make sure you do not keep importing and deleting the same bad files over and over. Files currently in the trash count as deleted.

-allow decompression bombs-

Some images, called Decompression Bombs, consume huge amounts of memory and CPU time (typically multiple GB and 30s+) to render. These can be malicious attacks or accidentally inelegant compressions of very large images (typically 100MegaPixel+ pngs). Keep this unchecked to catch and disallow them before they blat your computer.

-max gif size-

Some artists and over-enthusiastic fans re-encode popular webms into gif, typically so they can be viewed on simpler platforms like older phones. These people do not know what they are doing and generate 20MB, 100MB, even 220MB(!) gif files that they then upload to the boorus. Most hydrus users do not want these duplicate, bloated, bad-paletted, and CPU-laggy files on their clients, so this can probit them.

-archive all imports-

If this is set, all successful imports will be archived rather than sent to the inbox. This applies to files 'already in db' as well (these would otherwise retain their existing inbox status unaltered).

-presentation options-

For regular import pages, 'presentation' means if the imported file's thumbnail will be added. For quieter queues like subscriptions, it determines if the file will be in any popup message button.

If you have a very large (10k+ files) file import page, consider hiding some or all of its thumbs to reduce ui lag and increase overall import speed.'''
        
        wx.MessageBox( help_message )
        
    
    def GetValue( self ):
        
        exclude_deleted = self._exclude_deleted.GetValue()
        allow_decompression_bombs = self._allow_decompression_bombs.GetValue()
        min_size = self._min_size.GetValue()
        max_size = self._max_size.GetValue()
        max_gif_size = self._max_gif_size.GetValue()
        min_resolution = self._min_resolution.GetValue()
        max_resolution = self._max_resolution.GetValue()
        
        automatic_archive = self._auto_archive.GetValue()
        
        present_new_files = self._present_new_files.GetValue()
        present_already_in_inbox_files = self._present_already_in_inbox_files.GetValue()
        present_already_in_archive_files = self._present_already_in_archive_files.GetValue()
        
        file_import_options = ClientImportOptions.FileImportOptions()
        
        file_import_options.SetPreImportOptions( exclude_deleted, allow_decompression_bombs, min_size, max_size, max_gif_size, min_resolution, max_resolution )
        file_import_options.SetPostImportOptions( automatic_archive )
        file_import_options.SetPresentationOptions( present_new_files, present_already_in_inbox_files, present_already_in_archive_files )
        
        return file_import_options
        
    
class EditFrameLocationPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, info ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_info = info
        
        self._remember_size = wx.CheckBox( self, label = 'remember size' )
        self._remember_position = wx.CheckBox( self, label = 'remember position' )
        
        self._last_size = ClientGUICommon.NoneableSpinCtrl( self, 'last size', none_phrase = 'none set', min = 100, max = 1000000, unit = None, num_dimensions = 2 )
        self._last_position = ClientGUICommon.NoneableSpinCtrl( self, 'last position', none_phrase = 'none set', min = -1000000, max = 1000000, unit = None, num_dimensions = 2 )
        
        self._default_gravity_x = ClientGUICommon.BetterChoice( self )
        
        self._default_gravity_x.Append( 'by default, expand to width of parent', 1 )
        self._default_gravity_x.Append( 'by default, expand width as much as needed', -1 )
        
        self._default_gravity_y = ClientGUICommon.BetterChoice( self )
        
        self._default_gravity_y.Append( 'by default, expand to height of parent', 1 )
        self._default_gravity_y.Append( 'by default, expand height as much as needed', -1 )
        
        self._default_position = ClientGUICommon.BetterChoice( self )
        
        self._default_position.Append( 'by default, position off the top-left corner of parent', 'topleft' )
        self._default_position.Append( 'by default, position centered on the parent', 'center' )
        
        self._maximised = wx.CheckBox( self, label = 'start maximised' )
        self._fullscreen = wx.CheckBox( self, label = 'start fullscreen' )
        
        #
        
        ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = self._original_info
        
        self._remember_size.SetValue( remember_size )
        self._remember_position.SetValue( remember_position )
        
        self._last_size.SetValue( last_size )
        self._last_position.SetValue( last_position )
        
        ( x, y ) = default_gravity
        
        self._default_gravity_x.SelectClientData( x )
        self._default_gravity_y.SelectClientData( y )
        
        self._default_position.SelectClientData( default_position )
        
        self._maximised.SetValue( maximised )
        self._fullscreen.SetValue( fullscreen )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        text = 'Setting frame location info for ' + name + '.'
        
        vbox.Add( ClientGUICommon.BetterStaticText( self, text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._remember_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._remember_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._last_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._last_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._default_gravity_x, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._default_gravity_y, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._default_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._maximised, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._fullscreen, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen ) = self._original_info
        
        remember_size = self._remember_size.GetValue()
        remember_position = self._remember_position.GetValue()
        
        last_size = self._last_size.GetValue()
        last_position = self._last_position.GetValue()
        
        x = self._default_gravity_x.GetChoice()
        y = self._default_gravity_y.GetChoice()
        
        default_gravity = [ x, y ]
        
        default_position = self._default_position.GetChoice()
        
        maximised = self._maximised.GetValue()
        fullscreen = self._fullscreen.GetValue()
        
        return ( name, remember_size, remember_position, last_size, last_position, default_gravity, default_position, maximised, fullscreen )
        
    
class EditMediaViewOptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, info ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_info = info
        
        ( self._mime, media_show_action, preview_show_action, ( media_scale_up, media_scale_down, preview_scale_up, preview_scale_down, exact_zooms_only, scale_up_quality, scale_down_quality ) ) = self._original_info
        
        possible_actions = CC.media_viewer_capabilities[ self._mime ]
        
        self._media_show_action = ClientGUICommon.BetterChoice( self )
        self._preview_show_action = ClientGUICommon.BetterChoice( self )
        
        for action in possible_actions:
            
            self._media_show_action.Append( CC.media_viewer_action_string_lookup[ action ], action )
            
            if action != CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY:
                
                self._preview_show_action.Append( CC.media_viewer_action_string_lookup[ action ], action )
                
            
        
        self._media_show_action.Bind( wx.EVT_CHOICE, self.EventActionChange )
        self._preview_show_action.Bind( wx.EVT_CHOICE, self.EventActionChange )
        
        self._media_scale_up = ClientGUICommon.BetterChoice( self )
        self._media_scale_down = ClientGUICommon.BetterChoice( self )
        self._preview_scale_up = ClientGUICommon.BetterChoice( self )
        self._preview_scale_down = ClientGUICommon.BetterChoice( self )
        
        for scale_action in ( CC.MEDIA_VIEWER_SCALE_100, CC.MEDIA_VIEWER_SCALE_MAX_REGULAR, CC.MEDIA_VIEWER_SCALE_TO_CANVAS ):
            
            text = CC.media_viewer_scale_string_lookup[ scale_action ]
            
            self._media_scale_up.Append( text, scale_action )
            self._preview_scale_up.Append( text, scale_action )
            
            self._media_scale_down.Append( text, scale_action )
            self._preview_scale_down.Append( text, scale_action )
            
        
        self._exact_zooms_only = wx.CheckBox( self, label = 'only permit half and double zooms' )
        self._exact_zooms_only.SetToolTip( 'This limits zooms to 25%, 50%, 100%, 200%, 400%, and so on. It makes for fast resize and is useful for files that often have flat colours and hard edges, which often scale badly otherwise. The \'canvas fit\' zoom will still be inserted.' )
        
        self._scale_up_quality = ClientGUICommon.BetterChoice( self )
        
        for zoom in ( CC.ZOOM_NEAREST, CC.ZOOM_LINEAR, CC.ZOOM_CUBIC, CC.ZOOM_LANCZOS4 ):
            
            self._scale_up_quality.Append( CC.zoom_string_lookup[ zoom ], zoom )
            
        
        self._scale_down_quality = ClientGUICommon.BetterChoice( self )
        
        for zoom in ( CC.ZOOM_NEAREST, CC.ZOOM_LINEAR, CC.ZOOM_AREA ):
            
            self._scale_down_quality.Append( CC.zoom_string_lookup[ zoom ], zoom )
            
        
        #
        
        self._media_show_action.SelectClientData( media_show_action )
        self._preview_show_action.SelectClientData( preview_show_action )
        
        self._media_scale_up.SelectClientData( media_scale_up )
        self._media_scale_down.SelectClientData( media_scale_down )
        self._preview_scale_up.SelectClientData( preview_scale_up )
        self._preview_scale_down.SelectClientData( preview_scale_down )
        
        self._exact_zooms_only.SetValue( exact_zooms_only )
        
        self._scale_up_quality.SelectClientData( scale_up_quality )
        self._scale_down_quality.SelectClientData( scale_down_quality )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        text = 'Setting media view options for ' + HC.mime_string_lookup[ self._mime ] + '.'
        
        vbox.Add( ClientGUICommon.BetterStaticText( self, text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( ClientGUICommon.WrapInText( self._media_show_action, self, 'media viewer show action:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( ClientGUICommon.WrapInText( self._preview_show_action, self, 'preview show action:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        if possible_actions == CC.no_support:
            
            self._media_scale_up.Hide()
            self._media_scale_down.Hide()
            self._preview_scale_up.Hide()
            self._preview_scale_down.Hide()
            
            self._exact_zooms_only.Hide()
            
            self._scale_up_quality.Hide()
            self._scale_down_quality.Hide()
            
        else:
            
            rows = []
            
            rows.append( ( 'if the media is smaller than the media viewer canvas: ', self._media_scale_up ) )
            rows.append( ( 'if the media is larger than the media viewer canvas: ', self._media_scale_down ) )
            rows.append( ( 'if the media is smaller than the preview canvas: ', self._preview_scale_up) )
            rows.append( ( 'if the media is larger than the preview canvas: ', self._preview_scale_down ) )
            
            gridbox = ClientGUICommon.WrapInGrid( self, rows )
            
            vbox.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            vbox.Add( self._exact_zooms_only, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            vbox.Add( ClientGUICommon.BetterStaticText( self, 'Nearest neighbour is fast and ugly, 8x8 lanczos and area resampling are slower but beautiful.' ), CC.FLAGS_VCENTER )
            
            vbox.Add( ClientGUICommon.WrapInText( self._scale_up_quality, self, '>100% (interpolation) quality:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.Add( ClientGUICommon.WrapInText( self._scale_down_quality, self, '<100% (decimation) quality:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
        
        if self._mime == HC.APPLICATION_FLASH:
            
            self._scale_up_quality.Disable()
            self._scale_down_quality.Disable()
            
        
        self.SetSizer( vbox )
        
    
    def EventActionChange( self, event ):
        
        if self._media_show_action.GetChoice() in CC.no_support and self._preview_show_action.GetChoice() in CC.no_support:
            
            self._media_scale_up.Disable()
            self._media_scale_down.Disable()
            self._preview_scale_up.Disable()
            self._preview_scale_down.Disable()
            
            self._exact_zooms_only.Disable()
            
            self._scale_up_quality.Disable()
            self._scale_down_quality.Disable()
            
        else:
            
            self._media_scale_up.Enable()
            self._media_scale_down.Enable()
            self._preview_scale_up.Enable()
            self._preview_scale_down.Enable()
            
            self._exact_zooms_only.Enable()
            
            self._scale_up_quality.Enable()
            self._scale_down_quality.Enable()
            
        
        if self._mime == HC.APPLICATION_FLASH:
            
            self._scale_up_quality.Disable()
            self._scale_down_quality.Disable()
            
        
    
    def GetValue( self ):
        
        media_show_action = self._media_show_action.GetChoice()
        preview_show_action = self._preview_show_action.GetChoice()
        
        media_scale_up = self._media_scale_up.GetChoice()
        media_scale_down = self._media_scale_down.GetChoice()
        preview_scale_up = self._preview_scale_up.GetChoice()
        preview_scale_down = self._preview_scale_down.GetChoice()
        
        exact_zooms_only = self._exact_zooms_only.GetValue()
        
        scale_up_quality = self._scale_up_quality.GetChoice()
        scale_down_quality = self._scale_down_quality.GetChoice()
        
        return ( self._mime, media_show_action, preview_show_action, ( media_scale_up, media_scale_down, preview_scale_up, preview_scale_down, exact_zooms_only, scale_up_quality, scale_down_quality ) )
        
    
class EditNetworkContextPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, network_context, limited_types = None, allow_default = True ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        if limited_types is None:
            
            limited_types = ( CC.NETWORK_CONTEXT_GLOBAL, CC.NETWORK_CONTEXT_DOMAIN, CC.NETWORK_CONTEXT_HYDRUS, CC.NETWORK_CONTEXT_DOWNLOADER_PAGE, CC.NETWORK_CONTEXT_SUBSCRIPTION, CC.NETWORK_CONTEXT_WATCHER_PAGE )
            
        
        self._context_type = ClientGUICommon.BetterChoice( self )
        
        for ct in limited_types:
            
            self._context_type.Append( CC.network_context_type_string_lookup[ ct ], ct )
            
        
        self._context_type_info = ClientGUICommon.BetterStaticText( self )
        
        self._context_data_text = wx.TextCtrl( self )
        
        self._context_data_services = ClientGUICommon.BetterChoice( self )
        
        for service in HG.client_controller.services_manager.GetServices( HC.REPOSITORIES ):
            
            self._context_data_services.Append( service.GetName(), service.GetServiceKey() )
            
        
        self._context_data_subscriptions = ClientGUICommon.BetterChoice( self )
        
        self._context_data_none = wx.CheckBox( self, label = 'No specific data--acts as default.' )
        
        if not allow_default:
            
            self._context_data_none.Hide()
            
        
        names = HG.client_controller.Read( 'serialisable_names', HydrusSerialisable.SERIALISABLE_TYPE_SUBSCRIPTION )
        
        for name in names:
            
            self._context_data_subscriptions.Append( name, name )
            
        
        #
        
        self._context_type.SelectClientData( network_context.context_type )
        
        self._Update()
        
        context_type = network_context.context_type
        
        if network_context.context_data is None:
            
            self._context_data_none.SetValue( True )
            
        else:
            
            if context_type == CC.NETWORK_CONTEXT_DOMAIN:
                
                self._context_data_text.SetValue( network_context.context_data )
                
            elif context_type == CC.NETWORK_CONTEXT_HYDRUS:
                
                self._context_data_services.SelectClientData( network_context.context_data )
                
            elif context_type == CC.NETWORK_CONTEXT_SUBSCRIPTION:
                
                self._context_data_subscriptions.SelectClientData( network_context.context_data )
                
            
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._context_type, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._context_type_info, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._context_data_text, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._context_data_services, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._context_data_subscriptions, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._context_data_none, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        #
        
        self._context_type.Bind( wx.EVT_CHOICE, self.EventContextTypeChanged )
        
    
    def _Update( self ):
        
        self._context_type_info.SetLabelText( CC.network_context_type_description_lookup[ self._context_type.GetChoice() ] )
        
        context_type = self._context_type.GetChoice()
        
        self._context_data_text.Disable()
        self._context_data_services.Disable()
        self._context_data_subscriptions.Disable()
        
        if context_type in ( CC.NETWORK_CONTEXT_GLOBAL, CC.NETWORK_CONTEXT_DOWNLOADER_PAGE, CC.NETWORK_CONTEXT_WATCHER_PAGE ):
            
            self._context_data_none.SetValue( True )
            
        else:
            
            self._context_data_none.SetValue( False )
            
            if context_type == CC.NETWORK_CONTEXT_DOMAIN:
                
                self._context_data_text.Enable()
                
            elif context_type == CC.NETWORK_CONTEXT_HYDRUS:
                
                self._context_data_services.Enable()
                
            elif context_type == CC.NETWORK_CONTEXT_SUBSCRIPTION:
                
                self._context_data_subscriptions.Enable()
                
            
        
    
    def EventContextTypeChanged( self, event ):
        
        self._Update()
        
    
    def GetValue( self ):
        
        context_type = self._context_type.GetChoice()
        
        if self._context_data_none.GetValue() == True:
            
            context_data = None
            
        else:
            
            if context_type == CC.NETWORK_CONTEXT_DOMAIN:
                
                context_data = self._context_data_text.GetValue()
                
            elif context_type == CC.NETWORK_CONTEXT_HYDRUS:
                
                context_data = self._context_data_services.GetChoice()
                
            elif context_type == CC.NETWORK_CONTEXT_SUBSCRIPTION:
                
                context_data = self._context_data_subscriptions.GetChoice()
                
            
        
        return ClientNetworkingContexts.NetworkContext( context_type, context_data )
        
    
class EditNetworkContextCustomHeadersPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, network_contexts_to_custom_header_dicts ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._list_ctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
        
        self._list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._list_ctrl_panel, 'network_contexts_custom_headers', 15, 40, [ ( 'context', 24 ), ( 'header', 30 ), ( 'approved?', 12 ), ( 'reason', -1 ) ], self._ConvertDataToListCtrlTuples, delete_key_callback = self._Delete, activation_callback = self._Edit )
        
        self._list_ctrl_panel.SetListCtrl( self._list_ctrl )
        
        self._list_ctrl_panel.AddButton( 'add', self._Add )
        self._list_ctrl_panel.AddButton( 'edit', self._Edit, enabled_only_on_selection = True )
        self._list_ctrl_panel.AddButton( 'delete', self._Delete, enabled_only_on_selection = True )
        
        self._list_ctrl.Sort( 0 )
        
        #
        
        for ( network_context, custom_header_dict ) in network_contexts_to_custom_header_dicts.items():
            
            for ( key, ( value, approved, reason ) ) in custom_header_dict.items():
                
                data = ( network_context, ( key, value ), approved, reason )
                
                self._list_ctrl.AddDatas( ( data, ) )
                
            
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._list_ctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def _Add( self ):
        
        network_context = ClientNetworkingContexts.NetworkContext( CC.NETWORK_CONTEXT_DOMAIN, 'hostname.com' )
        key = 'Authorization'
        value = 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
        approved = ClientNetworkingDomain.VALID_APPROVED
        reason = 'EXAMPLE REASON: HTTP header login--needed for access.'
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit header' ) as dlg:
            
            panel = self._EditPanel( dlg, network_context, key, value, approved, reason )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                ( network_context, key, value, approved, reason ) = panel.GetValue()
                
                data = ( network_context, ( key, value ), approved, reason )
                
                self._list_ctrl.AddDatas( ( data, ) )
                
            
        
    
    def _ConvertDataToListCtrlTuples( self, data ):
        
        ( network_context, ( key, value ), approved, reason ) = data
        
        pretty_network_context = network_context.ToUnicode()
        
        pretty_key_value = key + ': ' + value
        
        pretty_approved = ClientNetworkingDomain.valid_str_lookup[ approved ]
        
        pretty_reason = reason
        
        display_tuple = ( pretty_network_context, pretty_key_value, pretty_approved, pretty_reason )
        
        sort_tuple = ( pretty_network_context, ( key, value ), pretty_approved, reason )
        
        return ( display_tuple, sort_tuple )
        
    
    def _Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._list_ctrl.DeleteSelected()
                
            
        
    
    def _Edit( self ):
        
        for data in self._list_ctrl.GetData( only_selected = True ):
            
            ( network_context, ( key, value ), approved, reason ) = data
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit header' ) as dlg:
                
                panel = self._EditPanel( dlg, network_context, key, value, approved, reason )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    self._list_ctrl.DeleteDatas( ( data, ) )
                    
                    ( network_context, key, value, approved, reason ) = panel.GetValue()
                    
                    new_data = ( network_context, ( key, value ), approved, reason )
                    
                    self._list_ctrl.AddDatas( ( new_data, ) )
                    
                else:
                    
                    break
                    
                
            
        
    
    def GetValue( self ):
        
        network_contexts_to_custom_header_dicts = collections.defaultdict( dict )
        
        for ( network_context, ( key, value ), approved, reason ) in self._list_ctrl.GetData():
            
            network_contexts_to_custom_header_dicts[ network_context ][ key ] = ( value, approved, reason )
            
        
        return network_contexts_to_custom_header_dicts
        
    
    class _EditPanel( ClientGUIScrolledPanels.EditPanel ):
        
        def __init__( self, parent, network_context, key, value, approved, reason ):
            
            ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
            
            self._network_context = ClientGUICommon.NetworkContextButton( self, network_context, limited_types = ( CC.NETWORK_CONTEXT_GLOBAL, CC.NETWORK_CONTEXT_DOMAIN ), allow_default = False )
            
            self._key = wx.TextCtrl( self )
            self._value = wx.TextCtrl( self )
            
            self._approved = ClientGUICommon.BetterChoice( self )
            
            for a in ( ClientNetworkingDomain.VALID_APPROVED, ClientNetworkingDomain.VALID_DENIED, ClientNetworkingDomain.VALID_UNKNOWN ):
                
                self._approved.Append( ClientNetworkingDomain.valid_str_lookup[ a ], a )
                
            
            self._reason = wx.TextCtrl( self )
            
            width = ClientGUICommon.ConvertTextToPixelWidth( self._reason, 60 )
            self._reason.SetMinSize( ( width, -1 ) )
            
            #
            
            self._key.SetValue( key )
            
            self._value.SetValue( value )
            
            self._approved.SelectClientData( approved )
            
            self._reason.SetValue( reason )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._network_context, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._key, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._value, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._approved, CC.FLAGS_EXPAND_PERPENDICULAR )
            vbox.Add( self._reason, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def GetValue( self ):
            
            network_context = self._network_context.GetValue()
            key = self._key.GetValue()
            value = self._value.GetValue()
            approved = self._approved.GetChoice()
            reason = self._reason.GetValue()
            
            return ( network_context, key, value, approved, reason )
            
        
    
class EditNoneableIntegerPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, value, message = '', none_phrase = 'no limit', min = 0, max = 1000000, unit = None, multiplier = 1, num_dimensions = 1 ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._value = ClientGUICommon.NoneableSpinCtrl( self, message = message, none_phrase = none_phrase, min = min, max = max, unit = unit, multiplier = multiplier, num_dimensions = num_dimensions )
        
        self._value.SetValue( value )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._value, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        return self._value.GetValue()
        
    
class EditRegexFavourites( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, regex_favourites ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._regexes = ClientGUIListCtrl.SaneListCtrl( self, 200, [ ( 'regex phrase', 120 ), ( 'description', -1 ) ], delete_key_callback = self.Delete, activation_callback = self.Edit )
        
        self._add_button = wx.Button( self, label = 'add' )
        self._add_button.Bind( wx.EVT_BUTTON, self.EventAdd )
        
        self._edit_button = wx.Button( self, label = 'edit' )
        self._edit_button.Bind( wx.EVT_BUTTON, self.EventEdit )
        
        self._delete_button = wx.Button( self, label = 'delete' )
        self._delete_button.Bind( wx.EVT_BUTTON, self.EventDelete )
        
        #
        
        for ( regex_phrase, description ) in regex_favourites:
            
            self._regexes.Append( ( regex_phrase, description ), ( regex_phrase, description ) )
            
        
        #
        
        regex_buttons = wx.BoxSizer( wx.HORIZONTAL )
        
        regex_buttons.Add( self._add_button, CC.FLAGS_VCENTER )
        regex_buttons.Add( self._edit_button, CC.FLAGS_VCENTER )
        regex_buttons.Add( self._delete_button, CC.FLAGS_VCENTER )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._regexes, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( regex_buttons, CC.FLAGS_BUTTON_SIZER )
        
        self.SetSizer( vbox )
        
    
    def Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._regexes.RemoveAllSelected()
                
            
        
    
    def Edit( self ):
        
        indices = self._regexes.GetAllSelected()
        
        for index in indices:
            
            ( regex_phrase, description ) = self._regexes.GetClientData( index )
            
            with ClientGUIDialogs.DialogTextEntry( self, 'Update regex.', default = regex_phrase ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    regex_phrase = dlg.GetValue()
                    
                    with ClientGUIDialogs.DialogTextEntry( self, 'Update description.', default = description ) as dlg_2:
                        
                        if dlg_2.ShowModal() == wx.ID_OK:
                            
                            description = dlg_2.GetValue()
                            
                            self._regexes.UpdateRow( index, ( regex_phrase, description ), ( regex_phrase, description ) )
                            
                        
                    
                
            
        
    
    def EventAdd( self, event ):
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter regex.' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                regex_phrase = dlg.GetValue()
                
                with ClientGUIDialogs.DialogTextEntry( self, 'Enter description.' ) as dlg_2:
                    
                    if dlg_2.ShowModal() == wx.ID_OK:
                        
                        description = dlg_2.GetValue()
                        
                        self._regexes.Append( ( regex_phrase, description ), ( regex_phrase, description ) )
                        
                    
                
            
        
    
    def EventDelete( self, event ):
        
        self.Delete()
        
    
    def EventEdit( self, event ):
        
        self.Edit()
        
    
    def GetValue( self ):
        
        return self._regexes.GetClientData()
        
    
class EditServersideService( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, serverside_service ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        duplicate_serverside_service = serverside_service.Duplicate()
        
        ( self._service_key, self._service_type, name, port, self._dictionary ) = duplicate_serverside_service.ToTuple()
        
        self._service_panel = self._ServicePanel( self, name, port, self._dictionary )
        
        self._panels = []
        
        if self._service_type in HC.RESTRICTED_SERVICES:
            
            self._panels.append( self._ServiceRestrictedPanel( self, self._dictionary ) )
            
            if self._service_type == HC.FILE_REPOSITORY:
                
                self._panels.append( self._ServiceFileRepositoryPanel( self, self._dictionary ) )
                
            
            if self._service_type == HC.SERVER_ADMIN:
                
                self._panels.append( self._ServiceServerAdminPanel( self, self._dictionary ) )
                
            
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._service_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        for panel in self._panels:
            
            vbox.Add( panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        self.SetSizer( vbox )
        
    
    def GetValue( self ):
        
        ( name, port, dictionary_part ) = self._service_panel.GetValue()
        
        dictionary = self._dictionary.Duplicate()
        
        dictionary.update( dictionary_part )
        
        for panel in self._panels:
            
            dictionary_part = panel.GetValue()
            
            dictionary.update( dictionary_part )
            
        
        return HydrusNetwork.GenerateService( self._service_key, self._service_type, name, port, dictionary )
        
    
    class _ServicePanel( ClientGUICommon.StaticBox ):
        
        def __init__( self, parent, name, port, dictionary ):
            
            ClientGUICommon.StaticBox.__init__( self, parent, 'basic information' )
            
            self._name = wx.TextCtrl( self )
            self._port = wx.SpinCtrl( self, min = 1, max = 65535 )
            self._upnp_port = ClientGUICommon.NoneableSpinCtrl( self, 'external upnp port', none_phrase = 'do not forward port', min = 1, max = 65535 )
            
            self._bandwidth_tracker_st = ClientGUICommon.BetterStaticText( self )
            
            #
            
            self._name.SetValue( name )
            self._port.SetValue( port )
            
            upnp_port = dictionary[ 'upnp_port' ]
            
            self._upnp_port.SetValue( upnp_port )
            
            bandwidth_tracker = dictionary[ 'bandwidth_tracker' ]
            
            bandwidth_text = bandwidth_tracker.GetCurrentMonthSummary()
            
            self._bandwidth_tracker_st.SetLabelText( bandwidth_text )
            
            #
            
            rows = []
            
            rows.append( ( 'name: ', self._name ) )
            rows.append( ( 'port: ', self._port ) )
            rows.append( ( 'upnp port: ', self._upnp_port ) )
            
            gridbox = ClientGUICommon.WrapInGrid( self, rows )
            
            self.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            self.Add( self._bandwidth_tracker_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        def GetValue( self ):
            
            dictionary_part = {}
            
            name = self._name.GetValue()
            port = self._port.GetValue()
            
            upnp_port = self._upnp_port.GetValue()
            
            dictionary_part[ 'upnp_port' ] = upnp_port
            
            return ( name, port, dictionary_part )
            
        
    
    class _ServiceRestrictedPanel( wx.Panel ):
        
        def __init__( self, parent, dictionary ):
            
            wx.Panel.__init__( self, parent )
            
            bandwidth_rules = dictionary[ 'bandwidth_rules' ]
            
            self._bandwidth_rules = ClientGUIControls.BandwidthRulesCtrl( self, bandwidth_rules )
            
            #
            
            vbox = wx.BoxSizer( wx.VERTICAL )
            
            vbox.Add( self._bandwidth_rules, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            self.SetSizer( vbox )
            
        
        def GetValue( self ):
            
            dictionary_part = {}
            
            dictionary_part[ 'bandwidth_rules' ] = self._bandwidth_rules.GetValue()
            
            return dictionary_part
            
        
    
    class _ServiceFileRepositoryPanel( ClientGUICommon.StaticBox ):
        
        def __init__( self, parent, dictionary ):
            
            ClientGUICommon.StaticBox.__init__( self, parent, 'file repository' )
            
            self._log_uploader_ips = wx.CheckBox( self )
            self._max_storage = ClientGUIControls.NoneableBytesControl( self, initial_value = 5 * 1024 * 1024 * 1024 )
            
            #
            
            log_uploader_ips = dictionary[ 'log_uploader_ips' ]
            max_storage = dictionary[ 'max_storage' ]
            
            self._log_uploader_ips.SetValue( log_uploader_ips )
            self._max_storage.SetValue( max_storage )
            
            #
            
            rows = []
            
            rows.append( ( 'log file uploader IP addresses?: ', self._log_uploader_ips ) )
            rows.append( ( 'max file storage: ', self._max_storage ) )
            
            gridbox = ClientGUICommon.WrapInGrid( self, rows )
            
            self.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
        
        def GetValue( self ):
            
            dictionary_part = {}
            
            log_uploader_ips = self._log_uploader_ips.GetValue()
            max_storage = self._max_storage.GetValue()
            
            dictionary_part[ 'log_uploader_ips' ] = log_uploader_ips
            dictionary_part[ 'max_storage' ] = max_storage
            
            return dictionary_part
            
        
    
    class _ServiceServerAdminPanel( ClientGUICommon.StaticBox ):
        
        def __init__( self, parent, dictionary ):
            
            ClientGUICommon.StaticBox.__init__( self, parent, 'server-wide bandwidth' )
            
            self._bandwidth_tracker_st = ClientGUICommon.BetterStaticText( self )
            
            bandwidth_rules = dictionary[ 'server_bandwidth_rules' ]
            
            self._bandwidth_rules = ClientGUIControls.BandwidthRulesCtrl( self, bandwidth_rules )
            
            #
            
            bandwidth_tracker = dictionary[ 'server_bandwidth_tracker' ]
            
            bandwidth_text = bandwidth_tracker.GetCurrentMonthSummary()
            
            self._bandwidth_tracker_st.SetLabelText( bandwidth_text )
            
            #
            
            self.Add( self._bandwidth_tracker_st, CC.FLAGS_EXPAND_PERPENDICULAR )
            self.Add( self._bandwidth_rules, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        def GetValue( self ):
            
            dictionary_part = {}
            
            bandwidth_rules = self._bandwidth_rules.GetValue()
            
            dictionary_part[ 'server_bandwidth_rules' ] = bandwidth_rules
            
            return dictionary_part
            
        
    
class EditSubscriptionPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, subscription ):
        
        subscription = subscription.Duplicate()
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_subscription = subscription
        
        #
        
        self._name = wx.TextCtrl( self )
        self._delay_st = ClientGUICommon.BetterStaticText( self )
        
        #
        
        self._query_panel = ClientGUICommon.StaticBox( self, 'site and queries' )
        
        self._site_type = ClientGUICommon.BetterChoice( self._query_panel )
        
        site_types = []
        site_types.append( HC.SITE_TYPE_BOORU )
        site_types.append( HC.SITE_TYPE_DEVIANT_ART )
        site_types.append( HC.SITE_TYPE_HENTAI_FOUNDRY_ARTIST )
        site_types.append( HC.SITE_TYPE_HENTAI_FOUNDRY_TAGS )
        site_types.append( HC.SITE_TYPE_NEWGROUNDS )
        site_types.append( HC.SITE_TYPE_PIXIV_ARTIST_ID )
        #site_types.append( HC.SITE_TYPE_PIXIV_TAG )
        site_types.append( HC.SITE_TYPE_TUMBLR )
        
        for site_type in site_types:
            
            self._site_type.Append( HC.site_type_string_lookup[ site_type ], site_type )
            
        
        self._site_type.Bind( wx.EVT_CHOICE, self.EventSiteChanged )
        
        self._booru_selector = wx.ListBox( self._query_panel )
        self._booru_selector.Bind( wx.EVT_LISTBOX, self.EventBooruSelected )
        
        queries_panel = ClientGUIListCtrl.BetterListCtrlPanel( self._query_panel )
        
        self._queries = ClientGUIListCtrl.BetterListCtrl( queries_panel, 'subscription_queries', 20, 20, [ ( 'query', 20 ), ( 'paused', 8 ), ( 'status', 8 ), ( 'last new file time', 20 ), ( 'last check time', 20 ), ( 'next check time', 20 ), ( 'file velocity', 20 ), ( 'recent delays', 20 ), ( 'items', 13 ) ], self._ConvertQueryToListCtrlTuples, delete_key_callback = self._DeleteQuery, activation_callback = self._EditQuery )
        
        queries_panel.SetListCtrl( self._queries )
        
        queries_panel.AddButton( 'add', self._AddQuery )
        queries_panel.AddButton( 'copy queries', self._CopyQueries, enabled_only_on_selection = True )
        queries_panel.AddButton( 'paste queries', self._PasteQueries )
        queries_panel.AddButton( 'edit', self._EditQuery, enabled_only_on_selection = True )
        queries_panel.AddButton( 'delete', self._DeleteQuery, enabled_only_on_selection = True )
        queries_panel.AddSeparator()
        queries_panel.AddButton( 'pause/play', self._PausePlay, enabled_only_on_selection = True )
        queries_panel.AddButton( 'retry failed', self._RetryFailed, enabled_check_func = self._ListCtrlCanRetryFailed )
        queries_panel.AddButton( 'retry ignored', self._RetryIgnored, enabled_check_func = self._ListCtrlCanRetryIgnored )
        queries_panel.AddButton( 'check now', self._CheckNow, enabled_check_func = self._ListCtrlCanCheckNow )
        queries_panel.AddButton( 'reset cache', self._ResetCache, enabled_check_func = self._ListCtrlCanResetCache )
        
        self._checker_options_button = ClientGUICommon.BetterButton( self._query_panel, 'edit check timings', self._EditCheckerOptions )
        
        #
        
        self._options_panel = ClientGUICommon.StaticBox( self, 'options' )
        
        self._initial_file_limit = ClientGUICommon.NoneableSpinCtrl( self._options_panel, '', none_phrase = 'get everything', min = 1, max = 1000000 )
        self._initial_file_limit.SetToolTip( 'If set, the first sync will add no more than this many files. Otherwise, it will get everything the gallery has.' )
        
        self._periodic_file_limit = ClientGUICommon.NoneableSpinCtrl( self._options_panel, '', none_phrase = 'get everything', min = 1, max = 1000000 )
        self._periodic_file_limit.SetToolTip( 'If set, normal syncs will add no more than this many files. Otherwise, they will get everything up until they find a file they have seen before.' )
        
        self._publish_files_to_popup_button = wx.CheckBox( self._options_panel )
        self._publish_files_to_page = wx.CheckBox( self._options_panel )
        self._merge_query_publish_events = wx.CheckBox( self._options_panel )
        
        tt = 'If unchecked, each query will produce its own \'subscription_name: query\' button or page.'
        
        self._merge_query_publish_events.SetToolTip( tt )
        
        #
        
        self._control_panel = ClientGUICommon.StaticBox( self, 'control' )
        
        self._paused = wx.CheckBox( self._control_panel )
        
        #
        
        ( name, gallery_identifier, gallery_stream_identifiers, queries, self._checker_options, initial_file_limit, periodic_file_limit, paused, file_import_options, tag_import_options, self._no_work_until, self._no_work_until_reason ) = subscription.ToTuple()
        
        self._file_import_options = ClientGUIImport.FileImportOptionsButton( self, file_import_options )
        
        ( namespaces, search_value ) = ClientDefaults.GetDefaultNamespacesAndSearchValue( gallery_identifier )
        
        self._tag_import_options = ClientGUIImport.TagImportOptionsButton( self, namespaces, tag_import_options, allow_default_selection = True )
        
        #
        
        self._name.SetValue( name )
        
        site_type = gallery_identifier.GetSiteType()
        
        self._site_type.SelectClientData( site_type )
        
        self._PresentForSiteType()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            booru_name = gallery_identifier.GetAdditionalInfo()
            
            index = self._booru_selector.FindString( booru_name )
            
            if index != wx.NOT_FOUND:
                
                self._booru_selector.Select( index )
                
            
        
        # set gallery_stream_identifiers selection here--some kind of list of checkboxes or whatever
        
        self._queries.AddDatas( queries )
        
        self._queries.Sort()
        
        self._initial_file_limit.SetValue( initial_file_limit )
        self._periodic_file_limit.SetValue( periodic_file_limit )
        
        ( publish_files_to_popup_button, publish_files_to_page, merge_query_publish_events ) = subscription.GetPresentationOptions()
        
        self._publish_files_to_popup_button.SetValue( publish_files_to_popup_button )
        self._publish_files_to_page.SetValue( publish_files_to_page )
        self._merge_query_publish_events.SetValue( merge_query_publish_events )
        
        self._paused.SetValue( paused )
        
        #
        
        self._query_panel.Add( self._site_type, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._query_panel.Add( self._booru_selector, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._query_panel.Add( queries_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        self._query_panel.Add( self._checker_options_button, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'on first check, get at most this many files: ', self._initial_file_limit ) )
        rows.append( ( 'on normal checks, get at most this many newer files: ', self._periodic_file_limit ) )
        rows.append( ( 'if new files imported, publish them to a popup button: ', self._publish_files_to_popup_button ) )
        rows.append( ( 'if new files imported, publish them to a page: ', self._publish_files_to_page ) )
        rows.append( ( 'publish all queries\' new files to the same page/popup button: ', self._merge_query_publish_events ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._options_panel, rows )
        
        self._options_panel.Add( ClientGUICommon.BetterStaticText( self._options_panel, 'If you are new to subscriptions, do not set these too high! In general, subscriptions that are larger than a couple of thousand files are a headache if they go wrong!' ), CC.FLAGS_EXPAND_PERPENDICULAR )
        self._options_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'currently paused: ', self._paused ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._control_panel, rows )
        
        self._control_panel.Add( gridbox, CC.FLAGS_LONE_BUTTON )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( ClientGUICommon.WrapInText( self._name, self, 'name: ' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.Add( self._delay_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._query_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( self._control_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._options_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._file_import_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._tag_import_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        self._UpdateDelayText()
        
    
    def _AddQuery( self ):
        
        gallery_identifier = self._GetGalleryIdentifier()
        
        ( namespaces, search_value ) = ClientDefaults.GetDefaultNamespacesAndSearchValue( gallery_identifier )
        
        query = ClientImporting.SubscriptionQuery( search_value )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit subscription query' ) as dlg:
            
            panel = EditSubscriptionQueryPanel( dlg, query )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                query = panel.GetValue()
                
                query_text = query.GetQueryText()
                
                if query_text in self._GetCurrentQueryTexts():
                    
                    wx.MessageBox( 'You already have a query for "' + query_text + '"! This duplicate entry you just created will not be added.' )
                    
                    return
                    
                
                self._queries.AddDatas( ( query, ) )
                
            
        
    
    def _CheckNow( self ):
        
        selected_queries = self._queries.GetData( only_selected = True )
        
        for query in selected_queries:
            
            query.CheckNow()
            
        
        self._queries.UpdateDatas( selected_queries )
        
        self._queries.Sort()
        
        self._no_work_until = 0
        
        self._UpdateDelayText()
        
    
    def _ConfigureTagImportOptions( self ):
        
        gallery_identifier = self._GetGalleryIdentifier()
        
        ( namespaces, search_value ) = ClientDefaults.GetDefaultNamespacesAndSearchValue( gallery_identifier )
        
        self._tag_import_options.SetNamespaces( namespaces )
        
    
    def _ConvertQueryToListCtrlTuples( self, query ):
        
        ( query_text, check_now, last_check_time, next_check_time, paused, status ) = query.ToTuple()
        
        pretty_query_text = query_text
        
        if paused:
            
            pretty_paused = 'yes'
            
        else:
            
            pretty_paused = ''
            
        
        if status == ClientImporting.CHECKER_STATUS_OK:
            
            pretty_status = 'ok'
            
        else:
            
            pretty_status = 'dead'
            
        
        file_seed_cache = query.GetFileSeedCache()
        
        last_new_file_time = file_seed_cache.GetLatestAddedTime()
        
        pretty_last_new_file_time = HydrusData.TimestampToPrettyTimeDelta( last_new_file_time )
        
        if last_check_time == 0 or last_check_time is None:
            
            pretty_last_check_time = '(initial check has not yet occured)'
            
        else:
            
            pretty_last_check_time = HydrusData.TimestampToPrettyTimeDelta( last_check_time )
            
        
        pretty_next_check_time = query.GetNextCheckStatusString()
        
        file_velocity = self._checker_options.GetRawCurrentVelocity( query.GetFileSeedCache(), last_check_time )
        pretty_file_velocity = self._checker_options.GetPrettyCurrentVelocity( query.GetFileSeedCache(), last_check_time, no_prefix = True )
        
        estimate = self._original_subscription.GetBandwidthWaitingEstimate( query )
        
        if estimate == 0:
            
            pretty_delay = ''
            delay = 0
            
        else:
            
            pretty_delay = 'bandwidth: ' + HydrusData.TimeDeltaToPrettyTimeDelta( estimate )
            delay = estimate
            
        
        ( file_status, simple_status, ( num_done, num_total ) ) = file_seed_cache.GetStatus()
        
        if num_total > 0:
            
            sort_float = float( num_done ) / num_total
            
        else:
            
            sort_float = 0.0
            
        
        items = ( sort_float, num_total, num_done )
        
        pretty_items = simple_status
        
        display_tuple = ( pretty_query_text, pretty_paused, pretty_status, pretty_last_new_file_time, pretty_last_check_time, pretty_next_check_time, pretty_file_velocity, pretty_delay, pretty_items )
        sort_tuple = ( query_text, paused, status, last_new_file_time, last_check_time, next_check_time, file_velocity, delay, items )
        
        return ( display_tuple, sort_tuple )
        
    
    def _CopyQueries( self ):
        
        query_texts = []
        
        for query in self._queries.GetData( only_selected = True ):
            
            query_texts.append( query.GetQueryText() )
            
        
        clipboard_text = os.linesep.join( query_texts )
        
        if len( clipboard_text ) > 0:
            
            HG.client_controller.pub( 'clipboard', 'text', clipboard_text )
            
        
    
    def _DeleteQuery( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Are you sure you want to delete all selected queries?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._queries.DeleteSelected()
                
            
        
    
    def _EditCheckerOptions( self ):
        
        with ClientGUITopLevelWindows.DialogEdit( self._checker_options_button, 'edit check timings' ) as dlg:
            
            panel = ClientGUITime.EditCheckerOptions( dlg, self._checker_options )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                self._checker_options = panel.GetValue()
                
                for query in self._queries.GetData():
                    
                    query.UpdateNextCheckTime( self._checker_options )
                    
                
                self._queries.UpdateDatas()
                
            
        
    
    def _EditQuery( self ):
        
        selected_queries = self._queries.GetData( only_selected = True )
        
        for old_query in selected_queries:
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit subscription query' ) as dlg:
                
                panel = EditSubscriptionQueryPanel( dlg, old_query )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    edited_query = panel.GetValue()
                    
                    edited_query_text = edited_query.GetQueryText()
                    
                    if edited_query_text != old_query.GetQueryText() and edited_query_text in self._GetCurrentQueryTexts():
                        
                        wx.MessageBox( 'You already have a query for "' + edited_query_text + '"! The edit you just made will not be saved.' )
                        
                        break
                        
                    
                    self._queries.DeleteDatas( ( old_query, ) )
                    
                    self._queries.AddDatas( ( edited_query, ) )
                    
                else:
                    
                    break
                    
                
            
        
        self._queries.Sort()
        
    
    def _GetCurrentQueryTexts( self ):
        
        query_strings = set()
        
        for query in self._queries.GetData():
            
            query_strings.add( query.GetQueryText() )
            
        
        return query_strings
        
    
    def _GetGalleryIdentifier( self ):
        
        site_type = self._site_type.GetChoice()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            booru_name = self._booru_selector.GetStringSelection()
            
            gallery_identifier = ClientDownloading.GalleryIdentifier( site_type, additional_info = booru_name )
            
        else:
            
            gallery_identifier = ClientDownloading.GalleryIdentifier( site_type )
            
        
        return gallery_identifier
        
    
    def _ListCtrlCanCheckNow( self ):
        
        for query in self._queries.GetData( only_selected = True ):
            
            if query.CanCheckNow():
                
                return True
                
            
        
        return False
        
    
    def _ListCtrlCanResetCache( self ):
        
        for query in self._queries.GetData( only_selected = True ):
            
            if not query.IsInitialSync():
                
                return True
                
            
        
        return False
        
    
    def _ListCtrlCanRetryFailed( self ):
        
        for query in self._queries.GetData( only_selected = True ):
            
            if query.CanRetryFailed():
                
                return True
                
            
        
        return False
        
    
    def _ListCtrlCanRetryIgnored( self ):
        
        for query in self._queries.GetData( only_selected = True ):
            
            if query.CanRetryIgnored():
                
                return True
                
            
        
        return False
        
    
    def _PasteQueries( self ):
        
        message = 'This will add new queries by pulling them from your clipboard. It assumes they are currently in your clipboard and newline separated. Is that ok?'
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() != wx.ID_YES:
                
                return
                
            
        
        text = HG.client_controller.GetClipboardText()
        
        try:
            
            query_texts = HydrusText.DeserialiseNewlinedTexts( text )
            
            current_query_texts = self._GetCurrentQueryTexts()
            
            already_existing_query_texts = list( current_query_texts.intersection( query_texts ) )
            new_query_texts = list( set( query_texts ).difference( current_query_texts ) )
            
            already_existing_query_texts.sort()
            new_query_texts.sort()
            
            if len( already_existing_query_texts ) > 0:
                
                message = 'The queries:'
                message += os.linesep * 2
                message += os.linesep.join( already_existing_query_texts )
                message += os.linesep * 2
                message += 'Were already in the subscription. They will not be added.'
                
                if len( new_query_texts ) > 0:
                    
                    message += os.linesep * 2
                    message += 'The queries:'
                    message += os.linesep * 2
                    message += os.linesep.join( new_query_texts )
                    message += os.linesep * 2
                    message += 'Were new and will be added.'
                    
                
                wx.MessageBox( message )
                
            
            queries = [ ClientImporting.SubscriptionQuery( query_text ) for query_text in new_query_texts ]
            
            self._queries.AddDatas( queries )
            
        except:
            
            wx.MessageBox( 'I could not understand what was in the clipboard' )
            
        
    
    def _PausePlay( self ):
        
        selected_queries = self._queries.GetData( only_selected = True )
        
        for query in selected_queries:
            
            query.PausePlay()
            
        
        self._queries.UpdateDatas( selected_queries )
        
    
    def _PresentForSiteType( self ):
        
        site_type = self._site_type.GetChoice()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            if self._booru_selector.GetCount() == 0:
                
                boorus = HG.client_controller.Read( 'remote_boorus' )
                
                names_and_boorus = list( boorus.items() )
                
                names_and_boorus.sort()
                
                for ( name, booru ) in names_and_boorus:
                    
                    self._booru_selector.Append( name, booru )
                    
                
                self._booru_selector.Select( 0 )
                
            
            self._booru_selector.Show()
            
        else:
            
            self._booru_selector.Hide()
            
        
        wx.CallAfter( self._ConfigureTagImportOptions )
        
        ClientGUITopLevelWindows.PostSizeChangedEvent( self )
        
    
    def _ResetCache( self ):
        
        message = '''Resetting these queries will delete all their cached urls, meaning when the subscription next runs, they will have to download all those links over again. This may be expensive in time and data. Only do this if you know what it means. Do you want to do it?'''
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                selected_queries = self._queries.GetData( only_selected = True )
                
                for query in selected_queries:
                    
                    query.Reset()
                    
                
                self._queries.UpdateDatas( selected_queries )
                
            
        
    
    def _RetryFailed( self ):
        
        selected_queries = self._queries.GetData( only_selected = True )
        
        for query in selected_queries:
            
            query.RetryFailures()
            
        
        self._queries.UpdateDatas( selected_queries )
        
        self._no_work_until = 0
        
        self._UpdateDelayText()
        
    
    def _RetryIgnored( self ):
        
        selected_queries = self._queries.GetData( only_selected = True )
        
        for query in selected_queries:
            
            query.RetryIgnored()
            
        
        self._queries.UpdateDatas( selected_queries )
        
    
    def _UpdateDelayText( self ):
        
        if HydrusData.TimeHasPassed( self._no_work_until ):
            
            status = 'no recent errors'
            
        else:
            
            status = 'delayed--retrying ' + HydrusData.TimestampToPrettyTimeDelta( self._no_work_until ) + ' because: ' + self._no_work_until_reason
            
        
        self._delay_st.SetLabelText( status )
        
    
    def EventBooruSelected( self, event ):
        
        self._ConfigureTagImportOptions()
        
    
    def EventSiteChanged( self, event ):
        
        self._PresentForSiteType()
        
    
    def GetValue( self ):
        
        name = self._name.GetValue()
        
        subscription = ClientImporting.Subscription( name )
        
        gallery_identifier = self._GetGalleryIdentifier()
        
        # in future, this can be harvested from some checkboxes or whatever for stream selection
        gallery_stream_identifiers = ClientDownloading.GetGalleryStreamIdentifiers( gallery_identifier )
        
        queries = self._queries.GetData()
        
        initial_file_limit = self._initial_file_limit.GetValue()
        periodic_file_limit = self._periodic_file_limit.GetValue()
        
        paused = self._paused.GetValue()
        
        file_import_options = self._file_import_options.GetValue()
        
        tag_import_options = self._tag_import_options.GetValue()
        
        subscription.SetTuple( gallery_identifier, gallery_stream_identifiers, queries, self._checker_options, initial_file_limit, periodic_file_limit, paused, file_import_options, tag_import_options, self._no_work_until )
        
        publish_files_to_popup_button = self._publish_files_to_popup_button.GetValue()
        publish_files_to_page = self._publish_files_to_page.GetValue()
        merge_query_publish_events = self._merge_query_publish_events.GetValue()
        
        subscription.SetPresentationOptions( publish_files_to_popup_button, publish_files_to_page, merge_query_publish_events )
        
        return subscription
        
    
class EditSubscriptionQueryPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, query ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_query = query
        
        self._status_st = ClientGUICommon.BetterStaticText( self )
        
        st_width = ClientGUICommon.ConvertTextToPixelWidth( self._status_st, 50 )
        
        self._status_st.SetMinSize( ( st_width, -1 ) )
        
        self._query_text = wx.TextCtrl( self )
        self._check_now = wx.CheckBox( self )
        self._paused = wx.CheckBox( self )
        
        self._file_seed_cache_control = ClientGUIFileSeedCache.FileSeedCacheStatusControl( self, HG.client_controller )
        
        self._gallery_seed_log_control = ClientGUIGallerySeedLog.GallerySeedLogStatusControl( self, HG.client_controller, True )
        
        #
        
        ( query_text, check_now, self._last_check_time, self._next_check_time, paused, self._status ) = self._original_query.ToTuple()
        
        self._query_text.SetValue( query_text )
        
        self._check_now.SetValue( check_now )
        
        self._paused.SetValue( paused )
        
        self._file_seed_cache = self._original_query.GetFileSeedCache().Duplicate()
        
        self._file_seed_cache_control.SetFileSeedCache( self._file_seed_cache )
        
        self._gallery_seed_log = self._original_query.GetGallerySeedLog().Duplicate()
        
        self._gallery_seed_log_control.SetGallerySeedLog( self._gallery_seed_log )
        
        #
        
        rows = []
        
        rows.append( ( 'query text: ', self._query_text ) )
        rows.append( ( 'check now: ', self._check_now ) )
        rows.append( ( 'paused: ', self._paused ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self, rows )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._status_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._file_seed_cache_control, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._gallery_seed_log_control, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        #
        
        self.Bind( wx.EVT_CHECKBOX, self.EventUpdate )
        
        self._UpdateStatus()
        
        self._query_text.SetSelection( -1, -1 ) # select all
        
        wx.CallAfter( self._query_text.SetFocus )
        
    
    def _GetValue( self ):
        
        query = self._original_query.Duplicate()
        
        query.SetQueryAndSeeds( self._query_text.GetValue(), self._file_seed_cache, self._gallery_seed_log )
        
        query.SetPaused( self._paused.GetValue() )
        
        query.SetCheckNow( self._check_now.GetValue() )
        
        return query
        
    
    def _UpdateStatus( self ):
        
        query = self._GetValue()
        
        self._status_st.SetLabelText( 'next check: ' + query.GetNextCheckStatusString() )
        
    
    def EventUpdate( self, event ):
        
        self._UpdateStatus()
        
    
    def GetValue( self ):
        
        query = self._GetValue()
        
        return query
        
    
class EditSubscriptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, subscriptions, subs_are_globally_paused = False ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        #
        
        menu_items = []
        
        page_func = HydrusData.Call( ClientPaths.LaunchPathInWebBrowser, os.path.join( HC.HELP_DIR, 'getting_started_subscriptions.html' ) )
        
        menu_items.append( ( 'normal', 'open the html subscriptions help', 'Open the help page for subscriptions in your web browesr.', page_func ) )
        
        help_button = ClientGUICommon.MenuBitmapButton( self, CC.GlobalBMPs.help, menu_items )
        
        help_hbox = ClientGUICommon.WrapInText( help_button, self, 'help for this panel -->', wx.Colour( 0, 0, 255 ) )
        
        subscriptions_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
        
        columns = [ ( 'name', -1 ), ( 'site', 20 ), ( 'query status', 25 ), ( 'last new file time', 20 ), ( 'last checked', 20 ), ( 'recent error/delay?', 20 ), ( 'items', 13 ), ( 'paused', 8 ) ]
        
        self._subscriptions = ClientGUIListCtrl.BetterListCtrl( subscriptions_panel, 'subscriptions', 25, 20, columns, self._ConvertSubscriptionToListCtrlTuples, delete_key_callback = self.Delete, activation_callback = self.Edit )
        
        subscriptions_panel.SetListCtrl( self._subscriptions )
        
        subscriptions_panel.AddButton( 'add', self.Add )
        
        menu_items = []
        
        menu_items.append( ( 'normal', 'to clipboard', 'Serialise the script and put it on your clipboard.', self.ExportToClipboard ) )
        menu_items.append( ( 'normal', 'to png', 'Serialise the script and encode it to an image file you can easily share with other hydrus users.', self.ExportToPng ) )
        
        subscriptions_panel.AddMenuButton( 'export', menu_items, enabled_only_on_selection = True )
        
        menu_items = []
        
        menu_items.append( ( 'normal', 'from clipboard', 'Load a script from text in your clipboard.', self.ImportFromClipboard ) )
        menu_items.append( ( 'normal', 'from png', 'Load a script from an encoded png.', self.ImportFromPng ) )
        
        subscriptions_panel.AddMenuButton( 'import', menu_items )
        subscriptions_panel.AddButton( 'duplicate', self.Duplicate, enabled_only_on_selection = True )
        subscriptions_panel.AddButton( 'edit', self.Edit, enabled_only_on_selection = True )
        subscriptions_panel.AddButton( 'delete', self.Delete, enabled_only_on_selection = True )
        
        subscriptions_panel.NewButtonRow()
        
        subscriptions_panel.AddButton( 'merge', self.Merge, enabled_check_func = self._CanMerge )
        subscriptions_panel.AddButton( 'separate', self.Separate, enabled_check_func = self._CanSeparate )
        
        subscriptions_panel.AddSeparator()
        
        subscriptions_panel.AddButton( 'pause/resume', self.PauseResume, enabled_only_on_selection = True )
        subscriptions_panel.AddButton( 'retry failures', self.RetryFailures, enabled_check_func = self._CanRetryFailures )
        subscriptions_panel.AddButton( 'retry ignored', self.RetryIgnored, enabled_check_func = self._CanRetryIgnored )
        subscriptions_panel.AddButton( 'scrub delays', self.ScrubDelays, enabled_check_func = self._CanScrubDelays )
        subscriptions_panel.AddButton( 'check queries now', self.CheckNow, enabled_check_func = self._CanCheckNow )
        
        if HG.client_controller.new_options.GetBoolean( 'advanced_mode' ):
            
            subscriptions_panel.AddButton( 'compact', self.Compact, enabled_check_func = self._CanCompact )
            
        
        subscriptions_panel.AddButton( 'reset', self.Reset, enabled_check_func = self._CanReset )
        
        subscriptions_panel.NewButtonRow()
        
        subscriptions_panel.AddButton( 'select subscriptions', self.SelectSubscriptions )
        subscriptions_panel.AddButton( 'overwrite checker timings', self.SetCheckerOptions, enabled_only_on_selection = True )
        subscriptions_panel.AddButton( 'overwrite tag import options', self.SetTagImportOptions, enabled_only_on_selection = True )
        
        #
        
        self._subscriptions.AddDatas( subscriptions )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( help_hbox, CC.FLAGS_BUTTON_SIZER )
        
        if subs_are_globally_paused:
            
            message = 'SUBSCRIPTIONS ARE CURRENTLY GLOBALLY PAUSED! CHECK THE NETWORK MENU TO UNPAUSE THEM.'
            
            st = ClientGUICommon.BetterStaticText( self, message )
            st.SetForegroundColour( ( 127, 0, 0 ) )
            
            vbox.Add( st, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        vbox.Add( subscriptions_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def _CanCheckNow( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanCheckNow() for subscription in subscriptions )
        
    
    def _CanCompact( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanCompact() for subscription in subscriptions )
        
    
    def _CanMerge( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        # only subs with queries can be merged
        
        subscriptions = [ subscription for subscription in subscriptions if len( subscription.GetQueries() ) > 0 ]
        
        gallery_identifiers = { subscription.GetGalleryIdentifier() for subscription in subscriptions }
        
        # if there are fewer, there must be dupes, so we must be able to merge
        
        return len( gallery_identifiers ) < len( subscriptions )
        
    
    def _CanReset( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanReset() for subscription in subscriptions )
        
    
    def _CanRetryFailures( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanRetryFailures() for subscription in subscriptions )
        
    
    def _CanRetryIgnored( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanRetryIgnored() for subscription in subscriptions )
        
    
    def _CanScrubDelays( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        return True in ( subscription.CanScrubDelay() for subscription in subscriptions )
        
    
    def _CanSeparate( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        if len( subscriptions ) != 1:
            
            return False
            
        
        subscription = subscriptions[0]
        
        if len( subscription.GetQueries() ) > 1:
            
            return True
            
        
        return False
        
    
    def _ConvertSubscriptionToListCtrlTuples( self, subscription ):
        
        ( name, gallery_identifier, gallery_stream_identifiers, queries, checker_options, initial_file_limit, periodic_file_limit, paused, file_import_options, tag_import_options, no_work_until, no_work_until_reason ) = subscription.ToTuple()
        
        pretty_site = gallery_identifier.ToString()
        
        period = 100
        pretty_period = 'fix this'
        
        if len( queries ) > 0:
            
            last_new_file_time = max( ( query.GetLatestAddedTime() for query in queries ) )
            pretty_last_new_file_time = HydrusData.TimestampToPrettyTimeDelta( last_new_file_time )
            
            last_checked = max( ( query.GetLastChecked() for query in queries ) )
            pretty_last_checked = HydrusData.TimestampToPrettyTimeDelta( last_checked )
            
        else:
            
            last_new_file_time = 0
            pretty_last_new_file_time = 'n/a'
            
            last_checked = 0
            pretty_last_checked = 'n/a'
            
        
        #
        
        num_queries = len( queries )
        num_dead = 0
        num_paused = 0
        
        for query in queries:
            
            if query.IsDead():
                
                num_dead += 1
                
            elif query.IsPaused():
                
                num_paused += 1
                
            
        
        num_ok = num_queries - ( num_dead + num_paused )
        
        status = ( num_queries, num_paused, num_dead )
        
        if num_queries == 0:
            
            pretty_status = 'no queries'
            
        else:
            
            status_components = [ HydrusData.ToHumanInt( num_ok ) + ' working' ]
            
            if num_paused > 0:
                
                status_components.append( HydrusData.ToHumanInt( num_paused ) + ' paused' )
                
            
            if num_dead > 0:
                
                status_components.append( HydrusData.ToHumanInt( num_dead ) + ' dead' )
                
            
            pretty_status = ', '.join( status_components )
            
        
        #
        
        if HydrusData.TimeHasPassed( no_work_until ):
            
            ( min_estimate, max_estimate ) = subscription.GetBandwidthWaitingEstimateMinMax()
            
            if max_estimate == 0: # don't seem to be any delays of any kind
                
                pretty_delay = ''
                delay = 0
                
            elif min_estimate == 0: # some are good to go, but there are delays
                
                pretty_delay = 'bandwidth: some ok, some up to ' + HydrusData.TimeDeltaToPrettyTimeDelta( max_estimate )
                delay = max_estimate
                
            else:
                
                if min_estimate == max_estimate: # probably just one query, and it is delayed
                    
                    pretty_delay = 'bandwidth: up to ' + HydrusData.TimeDeltaToPrettyTimeDelta( max_estimate )
                    delay = max_estimate
                    
                else:
                    
                    pretty_delay = 'bandwidth: from ' + HydrusData.TimeDeltaToPrettyTimeDelta( min_estimate ) + ' to ' + HydrusData.TimeDeltaToPrettyTimeDelta( max_estimate )
                    delay = max_estimate
                    
                
            
        else:
            
            pretty_delay = 'delayed--retrying ' + HydrusData.TimestampToPrettyTimeDelta( no_work_until ) + ' - because: ' + no_work_until_reason
            delay = HydrusData.GetTimeDeltaUntilTime( no_work_until )
            
        
        file_seed_caches = [ query.GetFileSeedCache() for query in queries ]
        
        ( queries_status, queries_simple_status, ( num_done, num_total ) ) = ClientImportFileSeeds.GenerateFileSeedCachesStatus( file_seed_caches )
        
        if num_total > 0:
            
            sort_float = float( num_done ) / num_total
            
        else:
            
            sort_float = 0.0
            
        
        items = ( sort_float, num_done, num_total )
        
        pretty_items = queries_simple_status
        
        if paused:
            
            pretty_paused = 'yes'
            
        else:
            
            pretty_paused = ''
            
        
        display_tuple = ( name, pretty_site, pretty_status, pretty_last_new_file_time, pretty_last_checked, pretty_delay, pretty_items, pretty_paused )
        sort_tuple = ( name, pretty_site, status, last_new_file_time, last_checked, delay, items, paused )
        
        return ( display_tuple, sort_tuple )
        
    
    def _GetExistingNames( self ):
        
        subscriptions = self._subscriptions.GetData()
        
        names = { subscription.GetName() for subscription in subscriptions }
        
        return names
        
    
    def _GetExportObject( self ):
        
        to_export = HydrusSerialisable.SerialisableList()
        
        for subscription in self._subscriptions.GetData( only_selected = True ):
            
            to_export.append( subscription )
            
        
        if len( to_export ) == 0:
            
            return None
            
        elif len( to_export ) == 1:
            
            return to_export[0]
            
        else:
            
            return to_export
            
        
    
    def _ImportObject( self, obj ):
        
        if isinstance( obj, HydrusSerialisable.SerialisableList ):
            
            for sub_obj in obj:
                
                self._ImportObject( sub_obj )
                
            
        else:
            
            if isinstance( obj, ClientImporting.Subscription ):
                
                subscription = obj
                
                subscription.SetNonDupeName( self._GetExistingNames() )
                
                self._subscriptions.AddDatas( ( subscription, ) )
                
            else:
                
                wx.MessageBox( 'That was not a subscription--it was a: ' + type( obj ).__name__ )
                
            
        
    
    def Add( self ):
        
        empty_subscription = ClientImporting.Subscription( 'new subscription' )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit subscription' ) as dlg_edit:
            
            panel = EditSubscriptionPanel( dlg_edit, empty_subscription )
            
            dlg_edit.SetPanel( panel )
            
            if dlg_edit.ShowModal() == wx.ID_OK:
                
                new_subscription = panel.GetValue()
                
                new_subscription.SetNonDupeName( self._GetExistingNames() )
                
                self._subscriptions.AddDatas( ( new_subscription, ) )
                
            
        
    
    def CheckNow( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subscriptions:
            
            subscription.CheckNow()
            
        
        self._subscriptions.UpdateDatas( subscriptions )
        
    
    def Compact( self ):
        
        message = 'WARNING! EXPERIMENTAL! This will tell all the select subscriptions to remove any processed urls old urls that it is no longer worth keeping around. It helps to keep subs clean and snappy on load/save.'
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                subscriptions = self._subscriptions.GetData( only_selected = True )
                
                for subscription in subscriptions:
                    
                    subscription.Compact()
                    
                
                self._subscriptions.UpdateDatas( subscriptions )
                
            
        
    
    def Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._subscriptions.DeleteSelected()
                
            
        
    
    def Duplicate( self ):
        
        subs_to_dupe = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subs_to_dupe:
            
            dupe_subscription = subscription.Duplicate()
            
            dupe_subscription.SetNonDupeName( self._GetExistingNames() )
            
            self._subscriptions.AddDatas( ( dupe_subscription, ) )
            
        
    
    def Edit( self ):
        
        subs_to_edit = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subs_to_edit:
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit subscription' ) as dlg:
                
                original_name = subscription.GetName()
                
                panel = EditSubscriptionPanel( dlg, subscription )
                
                dlg.SetPanel( panel )
                
                result = dlg.ShowModal()
                
                if result == wx.ID_OK:
                    
                    self._subscriptions.DeleteDatas( ( subscription, ) )
                    
                    edited_subscription = panel.GetValue()
                    
                    edited_subscription.SetNonDupeName( self._GetExistingNames() )
                    
                    self._subscriptions.AddDatas( ( edited_subscription, ) )
                    
                elif result == wx.ID_CANCEL:
                    
                    break
                    
                
            
        
        self._subscriptions.Sort()
        
    
    def ExportToClipboard( self ):
        
        export_object = self._GetExportObject()
        
        if export_object is not None:
            
            json = export_object.DumpToString()
            
            HG.client_controller.pub( 'clipboard', 'text', json )
            
        
    
    def ExportToPng( self ):
        
        export_object = self._GetExportObject()
        
        if export_object is not None:
            
            with ClientGUITopLevelWindows.DialogNullipotent( self, 'export to png' ) as dlg:
                
                panel = ClientGUISerialisable.PngExportPanel( dlg, export_object )
                
                dlg.SetPanel( panel )
                
                dlg.ShowModal()
                
            
        
    
    def GetValue( self ):
        
        subscriptions = self._subscriptions.GetData()
        
        return subscriptions
        
    
    def ImportFromClipboard( self ):
        
        raw_text = HG.client_controller.GetClipboardText()
        
        try:
            
            obj = HydrusSerialisable.CreateFromString( raw_text )
            
            self._ImportObject( obj )
            
        except Exception as e:
            
            wx.MessageBox( 'I could not understand what was in the clipboard' )
            
        
    
    def ImportFromPng( self ):
        
        with wx.FileDialog( self, 'select the png with the encoded script', wildcard = 'PNG (*.png)|*.png' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                path = HydrusData.ToUnicode( dlg.GetPath() )
                
                try:
                    
                    payload = ClientSerialisable.LoadFromPng( path )
                    
                except Exception as e:
                    
                    wx.MessageBox( HydrusData.ToUnicode( e ) )
                    
                    return
                    
                
                try:
                    
                    obj = HydrusSerialisable.CreateFromNetworkString( payload )
                    
                    self._ImportObject( obj )
                    
                except:
                    
                    wx.MessageBox( 'I could not understand what was encoded in the png!' )
                    
                
            
        
    
    def Merge( self ):
        
        message = 'Are you sure you want to merge the selected subscriptions? This will combine all selected subscriptions that share the same downloader, wrapping all their different queries into one subscription.'
        message += os.linesep * 2
        message += 'This is a big operation, so if it does not do what you expect, hit cancel afterwards!'
        message += os.linesep * 2
        message += 'Please note that all other subscription settings settings (like paused status and file limits and tag options) will be merged as well, so double-check your merged subs\' settings afterwards.'
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                to_be_merged_subs = self._subscriptions.GetData( only_selected = True )
                
                self._subscriptions.DeleteDatas( to_be_merged_subs )
                
                to_be_merged_subs = list( to_be_merged_subs )
                
                merged_subs = []
                
                while len( to_be_merged_subs ) > 1:
                    
                    primary_sub = to_be_merged_subs.pop()
                    
                    unmerged_subs = primary_sub.Merge( to_be_merged_subs )
                    
                    num_merged = len( to_be_merged_subs ) - len( unmerged_subs )
                    
                    if num_merged > 0:
                        
                        primary_sub_name = primary_sub.GetName()
                        
                        message = primary_sub_name + ' was able to merge ' + HydrusData.ToHumanInt( num_merged ) + ' other subscriptions. Would you like to give the merged subscription a new name?'
                        
                        with ClientGUIDialogs.DialogTextEntry( self, message, default = primary_sub_name ) as dlg:
                            
                            if dlg.ShowModal() == wx.ID_OK:
                                
                                name = dlg.GetValue()
                                
                                primary_sub.SetName( name )
                                
                            
                            # we cannot break safely here, so just do a 'don't rename' on cancel
                            
                        
                    
                    merged_subs.append( primary_sub )
                    
                    to_be_merged_subs = unmerged_subs
                    
                
                self._subscriptions.AddDatas( to_be_merged_subs )
                
                for merged_sub in merged_subs:
                    
                    merged_sub.SetNonDupeName( self._GetExistingNames() )
                    
                    self._subscriptions.AddDatas( ( merged_sub, ) )
                    
                
                self._subscriptions.Sort()
                
            
        
    
    def PauseResume( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subscriptions:
            
            subscription.PauseResume()
            
        
        self._subscriptions.UpdateDatas( subscriptions )
        
    
    def Reset( self ):
        
        message = '''Resetting these subscriptions will delete all their remembered urls, meaning when they next run, they will try to download them all over again. This may be expensive in time and data. Only do it if you are willing to wait. Do you want to do it?'''
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                subscriptions = self._subscriptions.GetData( only_selected = True )
                
                for subscription in subscriptions:
                    
                    subscription.Reset()
                    
                
                self._subscriptions.UpdateDatas( subscriptions )
                
            
        
    
    def RetryFailures( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subscriptions:
            
            subscription.RetryFailures()
            
        
        self._subscriptions.UpdateDatas( subscriptions )
        
    
    def RetryIgnored( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subscriptions:
            
            subscription.RetryIgnored()
            
        
        self._subscriptions.UpdateDatas( subscriptions )
        
    
    def ScrubDelays( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        for subscription in subscriptions:
            
            subscription.ScrubDelay()
            
        
        self._subscriptions.UpdateDatas( subscriptions )
        
    
    def SelectSubscriptions( self ):
        
        message = 'This selects subscriptions based on query text. Please enter some search text, and any subscription that has a query that includes that text will be selected.'
        
        with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                search_text = dlg.GetValue()
                
                self._subscriptions.SelectNone()
                
                selectee_subscriptions = []
                
                for subscription in self._subscriptions.GetData():
                    
                    if subscription.HasQuerySearchText( search_text ):
                        
                        selectee_subscriptions.append( subscription )
                        
                    
                
                self._subscriptions.SelectDatas( selectee_subscriptions )
                
            
        
    
    def Separate( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        if len( subscriptions ) != 1:
            
            wx.MessageBox( 'Separate only works if one subscription is selected!' )
            
            return
            
        
        subscription = subscriptions[0]
        
        num_queries = len( subscription.GetQueries() )
        
        if num_queries <= 1:
            
            wx.MessageBox( 'Separate only works if the selected subscription has more than one query!' )
            
            return
            
        
        if num_queries > 2:
            
            message = 'Are you sure you want to separate the selected subscriptions? Separating breaks merged subscriptions apart into smaller pieces.'
            yes_tuples = [ ( 'break the whole subscription up into single-query subscriptions', 'whole' ), ( 'only extract some of the subscription', 'part' ) ]
            
            with ClientGUIDialogs.DialogYesYesNo( self, message, yes_tuples = yes_tuples, no_label = 'forget it' ) as dlg:
                
                if dlg.ShowModal() == wx.ID_YES:
                    
                    action = dlg.GetValue()
                    
                else:
                    
                    return
                    
                
            
        else:
            
            action = 'whole'
            
        
        want_post_merge = False
        
        if action == 'part':
            
            queries = subscription.GetQueries()
            
            choice_tuples = [ ( query.GetQueryText(), query, False ) for query in queries ]
            
            with ClientGUIDialogs.DialogCheckFromList( self, 'select the queries to extract', choice_tuples ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    queries_to_extract = dlg.GetChecked()
                    
                else:
                    
                    return
                    
                
            
            if len( queries_to_extract ) == num_queries: # the madman selected them all
                
                action = 'whole'
                
            elif len( queries_to_extract ) > 1:
                
                yes_tuples = [ ( 'one new merged subscription', True ), ( 'many subscriptions with only one query', False ) ]
                
                message = 'Do you want the extracted queries to be a new merged subscription, or many subscriptions with only one query?'
                
                with ClientGUIDialogs.DialogYesYesNo( self, message, yes_tuples = yes_tuples, no_label = 'forget it' ) as dlg:
                    
                    if dlg.ShowModal() == wx.ID_YES:
                        
                        want_post_merge = dlg.GetValue()
                        
                    else:
                        
                        return
                        
                    
                
            
        
        if want_post_merge:
            
            message = 'Please enter the name for the new subscription.'
            
        else:
            
            message = 'Please enter the base name for the new subscriptions. They will be named \'[NAME]: query\'.'
            
        
        with ClientGUIDialogs.DialogTextEntry( self, message, default = subscription.GetName() ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                name = dlg.GetValue()
                
            else:
                
                return
                
            
        
        # ok, let's do it
        
        final_subscriptions = []
        
        self._subscriptions.DeleteDatas( ( subscription, ) )
        
        if action == 'whole':
            
            final_subscriptions.extend( subscription.Separate( name ) )
            
        else:
            
            extracted_subscriptions = list( subscription.Separate( name, queries_to_extract ) )
            
            if want_post_merge:
                
                primary_sub = extracted_subscriptions.pop()
                
                primary_sub.Merge( extracted_subscriptions )
                
                primary_sub.SetName( name )
                
                final_subscriptions.append( primary_sub )
                
            else:
                
                final_subscriptions.extend( extracted_subscriptions )
                
            
            final_subscriptions.append( subscription )
            
        
        for final_subscription in final_subscriptions:
            
            final_subscription.SetNonDupeName( self._GetExistingNames() )
            
            self._subscriptions.AddDatas( ( final_subscription, ) )
            
        
        self._subscriptions.Sort()
        
    
    def SetCheckerOptions( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        if len( subscriptions ) == 0:
            
            return
            
        
        checker_options = ClientDefaults.GetDefaultCheckerOptions( 'artist subscription' )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit check timings' ) as dlg:
            
            panel = ClientGUITime.EditCheckerOptions( dlg, checker_options )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                checker_options = panel.GetValue()
                
                for subscription in subscriptions:
                    
                    subscription.SetCheckerOptions( checker_options )
                    
                
                self._subscriptions.UpdateDatas( subscriptions )
                
            
        
    
    def SetTagImportOptions( self ):
        
        subscriptions = self._subscriptions.GetData( only_selected = True )
        
        if len( subscriptions ) == 0:
            
            return
            
        
        tag_import_options = HG.client_controller.network_engine.domain_manager.GetDefaultTagImportOptionsForPosts()
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit tag import options' ) as dlg:
            
            panel = EditTagImportOptionsPanel( dlg, [], tag_import_options, show_downloader_options = True, allow_default_selection = True )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                tag_import_options = panel.GetValue()
                
                for subscription in subscriptions:
                    
                    subscription.SetTagImportOptions( tag_import_options )
                    
                
                self._subscriptions.UpdateDatas( subscriptions )
                
            
        
    
class EditTagFilterPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, tag_filter, message = None ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        help_button = ClientGUICommon.BetterBitmapButton( self, CC.GlobalBMPs.help, self._ShowHelp )
        
        help_hbox = ClientGUICommon.WrapInText( help_button, self, 'help for this panel -->', wx.Colour( 0, 0, 255 ) )
        
        #
        
        blacklist_panel = ClientGUICommon.StaticBox( self, 'exclude these' )
        
        self._blacklist = ClientGUIListBoxes.ListBoxTagsCensorship( blacklist_panel )
        
        self._blacklist_input = wx.TextCtrl( blacklist_panel, style = wx.TE_PROCESS_ENTER )
        self._blacklist_input.Bind( wx.EVT_KEY_DOWN, self.EventKeyDownBlacklist )
        
        add_blacklist_button = ClientGUICommon.BetterButton( blacklist_panel, 'add', self._AddBlacklist )
        delete_blacklist_button = ClientGUICommon.BetterButton( blacklist_panel, 'delete', self._DeleteBlacklist )
        blacklist_everything_button = ClientGUICommon.BetterButton( blacklist_panel, 'block everything', self._BlacklistEverything )
        
        #
        
        whitelist_panel = ClientGUICommon.StaticBox( self, 'except for these' )
        
        self._whitelist = ClientGUIListBoxes.ListBoxTagsCensorship( whitelist_panel )
        
        self._whitelist_input = wx.TextCtrl( whitelist_panel, style = wx.TE_PROCESS_ENTER )
        self._whitelist_input.Bind( wx.EVT_KEY_DOWN, self.EventKeyDownWhitelist )
        
        add_whitelist_button = ClientGUICommon.BetterButton( whitelist_panel, 'add', self._AddWhitelist )
        delete_whitelist_button = ClientGUICommon.BetterButton( whitelist_panel, 'delete', self._DeleteWhitelist )
        
        #
        
        self._status_st = ClientGUICommon.BetterStaticText( self, 'currently keeping: ' )
        
        #
        
        blacklist_tag_slices = [ tag_slice for ( tag_slice, rule ) in tag_filter.GetTagSlicesToRules().items() if rule == CC.FILTER_BLACKLIST ]
        whitelist_tag_slices = [ tag_slice for ( tag_slice, rule ) in tag_filter.GetTagSlicesToRules().items() if rule == CC.FILTER_WHITELIST ]
        
        self._blacklist.AddTags( blacklist_tag_slices )
        self._whitelist.AddTags( whitelist_tag_slices )
        
        self._UpdateStatus()
        
        #
        
        button_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        button_hbox.Add( self._blacklist_input, CC.FLAGS_EXPAND_BOTH_WAYS )
        button_hbox.Add( add_blacklist_button, CC.FLAGS_VCENTER )
        button_hbox.Add( delete_blacklist_button, CC.FLAGS_VCENTER )
        button_hbox.Add( blacklist_everything_button, CC.FLAGS_VCENTER )
        
        blacklist_panel.Add( self._blacklist, CC.FLAGS_EXPAND_BOTH_WAYS )
        blacklist_panel.Add( button_hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        #
        
        button_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        button_hbox.Add( self._whitelist_input, CC.FLAGS_EXPAND_BOTH_WAYS )
        button_hbox.Add( add_whitelist_button, CC.FLAGS_VCENTER )
        button_hbox.Add( delete_whitelist_button, CC.FLAGS_VCENTER )
        
        whitelist_panel.Add( self._whitelist, CC.FLAGS_EXPAND_BOTH_WAYS )
        whitelist_panel.Add( button_hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        #
        
        hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        hbox.Add( blacklist_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        hbox.Add( whitelist_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( help_hbox, CC.FLAGS_BUTTON_SIZER )
        
        if message is not None:
            
            vbox.Add( ClientGUICommon.BetterStaticText( self, message ), CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        vbox.Add( hbox, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( self._status_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        #
        
        self.Bind( ClientGUIListBoxes.EVT_LIST_BOX, self.EventListBoxChanged )
        
    
    def _AddBlacklist( self ):
        
        tag_slice = self._blacklist_input.GetValue()
        
        self._blacklist.EnterTags( ( tag_slice, ) )
        
        self._whitelist.RemoveTags( ( tag_slice, ) )
        
        self._blacklist_input.SetValue( '' )
        
        self._UpdateStatus()
        
    
    def _AddWhitelist( self ):
        
        tag_slice = self._whitelist_input.GetValue()
        
        self._whitelist.EnterTags( ( tag_slice, ) )
        
        self._blacklist.RemoveTags( ( tag_slice, ) )
        
        self._whitelist_input.SetValue( '' )
        
        self._UpdateStatus()
        
    
    def _BlacklistEverything( self ):
        
        tag_slices = self._blacklist.GetClientData()
        
        self._blacklist.RemoveTags( tag_slices )
        
        self._blacklist.AddTags( ( '', ':' ) )
        
        self._UpdateStatus()
        
    
    def _DeleteBlacklist( self ):
        
        selected_tag_slices = self._blacklist.GetSelectedTags()
        
        if len( selected_tag_slices ) > 0:
            
            with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
                
                if dlg.ShowModal() == wx.ID_YES:
                    
                    self._blacklist.RemoveTags( selected_tag_slices )
                    
                
            
        
        self._UpdateStatus()
        
    
    def _DeleteWhitelist( self ):
        
        selected_tag_slices = self._whitelist.GetSelectedTags()
        
        if len( selected_tag_slices ) > 0:
            
            with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
                
                if dlg.ShowModal() == wx.ID_YES:
                    
                    self._whitelist.RemoveTags( selected_tag_slices )
                    
                
            
        
        self._UpdateStatus()
        
    
    def _ShowHelp( self ):
        
        help = 'Here you can set rules to filter tags. By default, all tags will be allowed.'
        help += os.linesep * 2
        help += 'Add tags or classes of tag to the left to exclude them. Here are the formats accepted:'
        help += os.linesep * 2
        help += '"tag" or "namespace:tag" - just a single tag'
        help += os.linesep
        help += '"namespace:" - all instances of that namespace'
        help += os.linesep
        help += '":" - all namespaced tags'
        help += os.linesep
        help += '"" (i.e. an empty string) - all unnamespaced tags'
        help += os.linesep * 2
        help += 'If you want to ban all of a class of tag except for some specific cases, add those specifics on the right to create exceptions for them.'
        help += os.linesep * 2
        help += 'If you want to make this work like a whitelist, hit \'block everything\' (to block everything on the left) and then add what you do want on the right.'
        
        wx.MessageBox( help )
        
    
    def _UpdateStatus( self ):
        
        tag_filter = self.GetValue()
        
        pretty_tag_filter = tag_filter.ToPermittedString()
        
        self._status_st.SetLabelText( 'currently keeping: ' + pretty_tag_filter )
        
    
    def EventListBoxChanged( self, event ):
        
        self._UpdateStatus()
        
    
    def EventKeyDownBlacklist( self, event ):
        
        ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
        
        if key in ( wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ):
            
            self._AddBlacklist()
            
        else:
            
            event.Skip()
            
        
    
    def EventKeyDownWhitelist( self, event ):
        
        ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
        
        if key in ( wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ):
            
            self._AddWhitelist()
            
        else:
            
            event.Skip()
            
        
    
    def GetValue( self ):
        
        tag_filter = ClientTags.TagFilter()
        
        for tag_slice in self._blacklist.GetClientData():
            
            tag_filter.SetRule( tag_slice, CC.FILTER_BLACKLIST )
            
        
        for tag_slice in self._whitelist.GetClientData():
            
            tag_filter.SetRule( tag_slice, CC.FILTER_WHITELIST )
            
        
        return tag_filter
        
    
class EditTagImportOptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, namespaces, tag_import_options, show_downloader_options = True, allow_default_selection = False ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._service_keys_to_service_tag_import_options_panels = {}
        
        #
        
        help_button = ClientGUICommon.BetterBitmapButton( self, CC.GlobalBMPs.help, self._ShowHelp )
        help_button.SetToolTip( 'Show help regarding these tag options.' )
        
        #
        
        is_default_panel = ClientGUICommon.StaticBox( self, 'use default' )
        
        self._is_default = wx.CheckBox( is_default_panel )
        
        tt = '(This only works for the new download system! If you are not sure this context uses the new downloader, test it on a small scale first!)'
        tt += os.linesep * 2
        tt += 'If this is checked, the client will refer to the defaults (as set under "network->downloaders->manage default tag import options") for the appropriate tag import options at the time of import.'
        tt += os.linesep * 2
        tt += 'It is easier to manage tag import options by relying on the defaults, since any change in the single default location will update all the eventual import queues that refer to those defaults, whereas having specific options for every subscription or downloader means making an update to the blacklist or tag filter needs to be repeated dozens or hundreds of times.'
        tt += os.linesep * 2
        tt += 'But if you are doing a one-time import that has some unusual tag rules, uncheck this and set those specific rules here.'
        
        self._is_default.SetToolTip( tt )
        
        #
        
        self._specific_options_panel = wx.Panel( self )
        
        #
        
        downloader_options_panel = ClientGUICommon.StaticBox( self._specific_options_panel, 'fetch options' )
        
        self._fetch_tags_even_if_url_recognised_and_file_already_in_db = wx.CheckBox( downloader_options_panel )
        self._fetch_tags_even_if_hash_recognised_and_file_already_in_db = wx.CheckBox( downloader_options_panel )
        
        tag_blacklist = tag_import_options.GetTagBlacklist()
        
        message = 'Blacklists are managed by the tag filtering object, which has an overcomplicated ui for this typically simple job.'
        message += os.linesep * 2
        message += 'Any tag that this filter excludes will be considered a blacklisted tag and will stop the file importing.'
        message += os.linesep * 2
        message += 'So if you only want to stop \'scat\' or \'gore\', just add them to the left column and hit ok.'
        
        self._tag_filter_button = ClientGUICommon.TagFilterButton( downloader_options_panel, message, tag_blacklist, is_blacklist = True )
        self._tag_filter_button.SetToolTip( 'If a blacklist is set, any file that has any of the specified tags will not be imported. This typically avoids the bandwidth of downloading the file, as well.' )
        
        self._services_vbox = wx.BoxSizer( wx.VERTICAL )
        
        #
        
        self._is_default.SetValue( tag_import_options.IsDefault() )
        
        self._fetch_tags_even_if_url_recognised_and_file_already_in_db.SetValue( tag_import_options.ShouldFetchTagsEvenIfURLKnownAndFileAlreadyInDB() )
        self._fetch_tags_even_if_hash_recognised_and_file_already_in_db.SetValue( tag_import_options.ShouldFetchTagsEvenIfHashKnownAndFileAlreadyInDB() )
        
        self._InitialiseServices( tag_import_options, namespaces, show_downloader_options )
        
        #
        
        rows = []
        
        rows.append( ( 'rely on the appropriate default tag import options at the time of import: ', self._is_default ) )
        
        gridbox = ClientGUICommon.WrapInGrid( is_default_panel, rows )
        
        is_default_panel.Add( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        if not allow_default_selection:
            
            is_default_panel.Hide()
            
        
        #
        
        rows = []
        
        rows.append( ( 'fetch tags even if url recognised and file already in db: ', self._fetch_tags_even_if_url_recognised_and_file_already_in_db ) )
        rows.append( ( 'fetch tags even if hash recognised and file already in db: ', self._fetch_tags_even_if_hash_recognised_and_file_already_in_db ) )
        rows.append( ( 'set blacklist: ', self._tag_filter_button ) )
        
        gridbox = ClientGUICommon.WrapInGrid( downloader_options_panel, rows )
        
        downloader_options_panel.Add( gridbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        if not show_downloader_options:
            
            downloader_options_panel.Hide()
            
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( downloader_options_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._services_vbox, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        
        self._specific_options_panel.SetSizer( vbox )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( help_button, CC.FLAGS_LONE_BUTTON )
        vbox.Add( is_default_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._specific_options_panel, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        #
        
        self._is_default.Bind( wx.EVT_CHECKBOX, self.EventIsDefault )
        
        self._UpdateIsDefault()
        
    
    def _InitialiseServices( self, tag_import_options, namespaces, show_downloader_options ):
        
        namespaces = list( namespaces )
        
        namespaces.sort()
        
        services = HG.client_controller.services_manager.GetServices( HC.TAG_SERVICES, randomised = False )
        
        for service in services:
            
            service_key = service.GetServiceKey()
            
            service_tag_import_options = tag_import_options.GetServiceTagImportOptions( service_key )
            
            panel = EditServiceTagImportOptionsPanel( self._specific_options_panel, service_key, namespaces, service_tag_import_options, show_downloader_options = show_downloader_options )
            
            self._service_keys_to_service_tag_import_options_panels[ service_key ] = panel
            
            self._services_vbox.Add( panel, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
    
    def _ShowHelp( self ):
        
        message = '''Here you can select which kinds of tags you would like applied to the files that are imported.

If this import context can fetch and parse tags from a remote location (such as a gallery downloader, which may provide 'creator' or 'series' tags, amongst others), then the namespaces it provides will be listed here with checkboxes--simply check which ones you are interested in for the tag services you want them to be applied to and it will all occur as the importer processes its files.

In these cases, if the URL has been previously downloaded and the client knows its file is already in the database, the client will usually not make a new network request to fetch the file's tags. This allows for quick reprocessing/skipping of previously seen items in large download queues and saves bandwidth. If you however wish to purposely fetch tags for files you have previously downloaded, you can also force tag fetching for these 'already in db' files.

I strongly recommend that you only ever turn this 'fetch tags even...' option for one-time jobs. It is typically only useful if you download some files and realised you forgot to set the tag parsing options you like--you can set the fetch option on and 'try again' the files to force the downloader to fetch the tags.

You can also set some fixed 'explicit' tags (like, say, 'read later' or 'from my unsorted folder' or 'pixiv subscription') to be applied to all imported files.

---

Please note that you can set up the 'default' values for these tag import options under _network->downloaders->manage default tag import options_, both globally and on a per-parser basis. If you always want all the tags going to 'local tags', this is easy to set up there, and you won't have to put it in every time.'''
        
        wx.MessageBox( message )
        
    
    def _UpdateIsDefault( self ):
        
        is_default = self._is_default.GetValue()
        
        show_specific_options = not is_default
        
        self._specific_options_panel.Enable( show_specific_options )
        
    
    def EventIsDefault( self, event ):
        
        self._UpdateIsDefault()
        
    
    def GetValue( self ):
        
        is_default = self._is_default.GetValue()
        
        if is_default:
            
            tag_import_options = ClientImportOptions.TagImportOptions( is_default = True )
            
        else:
            
            fetch_tags_even_if_url_recognised_and_file_already_in_db = self._fetch_tags_even_if_url_recognised_and_file_already_in_db.GetValue()
            fetch_tags_even_if_hash_recognised_and_file_already_in_db = self._fetch_tags_even_if_hash_recognised_and_file_already_in_db.GetValue()
            
            service_keys_to_service_tag_import_options = { service_key : panel.GetValue() for ( service_key, panel ) in self._service_keys_to_service_tag_import_options_panels.items() }
            
            tag_blacklist = self._tag_filter_button.GetValue()
            
            tag_import_options = ClientImportOptions.TagImportOptions( fetch_tags_even_if_url_recognised_and_file_already_in_db = fetch_tags_even_if_url_recognised_and_file_already_in_db, fetch_tags_even_if_hash_recognised_and_file_already_in_db = fetch_tags_even_if_hash_recognised_and_file_already_in_db, tag_blacklist = tag_blacklist, service_keys_to_service_tag_import_options = service_keys_to_service_tag_import_options )
            
        
        return tag_import_options
        
    
class EditServiceTagImportOptionsPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, service_key, possible_namespaces, service_tag_import_options, show_downloader_options = True ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._service_key = service_key
        
        self._namespaces_to_checkbox_info = {}
        
        name = HG.client_controller.services_manager.GetName( self._service_key )
        
        main_box = ClientGUICommon.StaticBox( self, name )
        
        #
        
        ( get_all, get_all_filter, namespaces, self._additional_tags, self._to_new_files, self._to_already_in_inbox, self._to_already_in_archive, self._only_add_existing_tags, self._only_add_existing_tags_filter ) = service_tag_import_options.ToTuple()
        
        #
        
        menu_items = self._GetCogIconMenuItems()
        
        cog_button = ClientGUICommon.MenuBitmapButton( main_box, CC.GlobalBMPs.cog, menu_items )
        
        #
        
        downloader_options_panel = ClientGUICommon.StaticBox( main_box, 'tag parsing' )
        
        if len( possible_namespaces ) > 0:
            
            label = 'get tags (works better than \'select all\' for the new downloader system)'
            
        else:
            
            label = 'get tags'
            
        
        self._get_all_checkbox = wx.CheckBox( downloader_options_panel, label = label )
        
        message = 'You can filter which tags are applied here. For instance, you might want to say \'only "character:", "creator:" and "series:" tags\', or \'everything _except_ "species:" tags\'.'
        message += os.linesep * 2
        message += 'This panel can get pretty complicated--down to individual tags. You probably don\'t want the hassle of managing hundreds of individual tags in a whitelist here, but it is possible.'
        message += os.linesep * 2
        message += 'I recommend you stick to broad namespaces. The easy way to create a simple whitelist is to click \'block everything\' and then put in what you _want_ on the right.'
        
        self._get_all_filter_button = ClientGUICommon.TagFilterButton( downloader_options_panel, message, get_all_filter )
        
        hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        hbox.Add( self._get_all_checkbox, CC.FLAGS_VCENTER )
        hbox.Add( self._get_all_filter_button, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        downloader_options_panel.Add( hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        if len( possible_namespaces ) == 1:
            
            downloader_options_panel.Add( ClientGUICommon.BetterStaticText( downloader_options_panel, '----' ), CC.FLAGS_EXPAND_PERPENDICULAR )
            
        elif len( possible_namespaces ) > 1:
            
            select_all_button = ClientGUICommon.BetterButton( downloader_options_panel, 'select all', self._SelectAll, True )
            select_none_button = ClientGUICommon.BetterButton( downloader_options_panel, 'select none', self._SelectAll, False )
            
            hbox = wx.BoxSizer( wx.HORIZONTAL )
            
            hbox.Add( select_all_button, CC.FLAGS_EXPAND_BOTH_WAYS )
            hbox.Add( select_none_button, CC.FLAGS_EXPAND_BOTH_WAYS )
            
            downloader_options_panel.Add( hbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
        
        for possible_namespace in possible_namespaces:
            
            label = ClientTags.RenderNamespaceForUser( possible_namespace )
            
            namespace_checkbox = wx.CheckBox( downloader_options_panel, label = label )
            
            namespace_checkbox.SetValue( possible_namespace in namespaces )
            
            self._namespaces_to_checkbox_info[ possible_namespace ] = namespace_checkbox
            
            downloader_options_panel.Add( namespace_checkbox, CC.FLAGS_EXPAND_PERPENDICULAR )
            
        
        #
        
        button_label = HydrusData.ToHumanInt( len( self._additional_tags ) ) + ' additional tags'
        
        self._additional_button = ClientGUICommon.BetterButton( main_box, button_label, self._DoAdditionalTags )
        
        #
        
        self._get_all_checkbox.SetValue( get_all )
        
        #
        
        if not show_downloader_options:
            
            downloader_options_panel.Hide()
            
        
        main_box.Add( cog_button, CC.FLAGS_LONE_BUTTON )
        main_box.Add( downloader_options_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        main_box.Add( self._additional_button, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( main_box, CC.FLAGS_EXPAND_SIZER_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self._UpdateGetAllCheckboxes()
        
        #
        
        self._get_all_checkbox.Bind( wx.EVT_CHECKBOX, self.EventGetAllCheckbox )
        
    
    def _DoAdditionalTags( self ):
        
        message = 'Any tags you enter here will be applied to every file that passes through this import context.'
        
        with ClientGUIDialogs.DialogInputTags( self, self._service_key, list( self._additional_tags ), message = message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                self._additional_tags = dlg.GetTags()
                
            
        
        button_label = HydrusData.ToHumanInt( len( self._additional_tags ) ) + ' additional tags'
        
        self._additional_button.SetLabelText( button_label )
        
    
    def _EditOnlyAddExistingTagsFilter( self ):
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit already-exist filter' ) as dlg:
            
            message = 'If you do not want the \'only add tags that already exist\' option to apply to all tags coming in, set a filter here for the tags you _want_ to be exposed to this filter.'
            message += os.linesep * 2
            message += 'For instance, if you only want the wash of messy unnamespaced tags to be filtered, then just add \':\' (for all namespaces) to the \'exclude\' box and you should be good.'
            message += os.linesep * 2
            message += 'This is obviously a complicated idea, so make sure you test it on a small scale before you try anything big.'
            message += os.linesep * 2
            message += 'Clicking ok on this dialog will automatically turn on the already-exists filter if it is off.'
            
            panel = EditTagFilterPanel( dlg, self._only_add_existing_tags_filter, message )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                self._only_add_existing_tags_filter = panel.GetValue()
                
                self._only_add_existing_tags = True
                
            
        
    
    def _GetCogIconMenuItems( self ):
        
        menu_items = []
        
        check_manager = ClientGUICommon.CheckboxManagerBoolean( self, '_to_new_files' )
        
        menu_items.append( ( 'check', 'apply tags to new files', 'Apply tags to new files.', check_manager ) )
        
        check_manager = ClientGUICommon.CheckboxManagerBoolean( self, '_to_already_in_inbox' )
        
        menu_items.append( ( 'check', 'apply tags to files already in inbox', 'Apply tags to files that are already in the db and in the inbox.', check_manager ) )
        
        check_manager = ClientGUICommon.CheckboxManagerBoolean( self, '_to_already_in_archive' )
        
        menu_items.append( ( 'check', 'apply tags to files already in archive', 'Apply tags to files that are already in the db and archived.', check_manager ) )
        
        menu_items.append( ( 'separator', 0, 0, 0 ) )
        
        check_manager = ClientGUICommon.CheckboxManagerBoolean( self, '_only_add_existing_tags' )
        
        menu_items.append( ( 'check', 'only add tags that already exist', 'Only add tags to this service if they have non-zero count.', check_manager ) )
        
        menu_items.append( ( 'normal', 'set a filter for already-exist test', 'Tell the already-exist test to only work on a subset of tags.', self._EditOnlyAddExistingTagsFilter ) )
        
        return menu_items
        
    
    def _SelectAll( self, value ):
        
        for checkbox in self._namespaces_to_checkbox_info.values():
            
            checkbox.SetValue( value )
            
        
    
    def _UpdateGetAllCheckboxes( self ):
        
        get_all = self._get_all_checkbox.GetValue()
        
        should_enable_filter = get_all
        
        self._get_all_filter_button.Enable( should_enable_filter )
        
        should_enable_checkboxes = not get_all
        
        for checkbox in self._namespaces_to_checkbox_info.values():
            
            checkbox.Enable( should_enable_checkboxes )
            
        
    
    def EventGetAllCheckbox( self, event ):
        
        self._UpdateGetAllCheckboxes()
        
    
    def GetValue( self ):
        
        get_all = self._get_all_checkbox.GetValue()
        namespaces = [ namespace for ( namespace, checkbox ) in self._namespaces_to_checkbox_info.items() if checkbox.GetValue() ]
        
        get_all_filter = self._get_all_filter_button.GetValue()
        
        service_tag_import_options = ClientImportOptions.ServiceTagImportOptions( get_all = get_all, get_all_filter = get_all_filter, namespaces = namespaces, additional_tags = self._additional_tags, to_new_files = self._to_new_files, to_already_in_inbox = self._to_already_in_inbox, to_already_in_archive = self._to_already_in_archive, only_add_existing_tags = self._only_add_existing_tags, only_add_existing_tags_filter = self._only_add_existing_tags_filter )
        
        return service_tag_import_options
        
    
class EditTagSummaryGeneratorPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, tag_summary_generator ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        show_panel = ClientGUICommon.StaticBox( self, 'shows' )
        
        self._show = wx.CheckBox( show_panel )
        
        edit_panel = ClientGUICommon.StaticBox( self, 'edit' )
        
        self._background_colour = ClientGUICommon.AlphaColourControl( edit_panel )
        self._text_colour = ClientGUICommon.AlphaColourControl( edit_panel )
        
        self._namespaces_listbox = ClientGUIListBoxes.QueueListBox( edit_panel, 8, self._ConvertNamespaceToListBoxString, self._AddNamespaceInfo, self._EditNamespaceInfo )
        
        self._separator = wx.TextCtrl( edit_panel )
        
        example_panel = ClientGUICommon.StaticBox( self, 'example' )
        
        self._example_tags = wx.TextCtrl( example_panel, style = wx.TE_MULTILINE )
        
        self._test_result = wx.TextCtrl( example_panel, style = wx.TE_READONLY )
        
        #
        
        ( background_colour, text_colour, namespace_info, separator, example_tags, show ) = tag_summary_generator.ToTuple()
        
        self._show.SetValue( show )
        
        self._background_colour.SetValue( background_colour )
        self._text_colour.SetValue( text_colour )
        self._namespaces_listbox.AddDatas( namespace_info )
        self._separator.SetValue( separator )
        self._example_tags.SetValue( os.linesep.join( example_tags ) )
        
        self._UpdateTest()
        
        #
        
        rows = []
        
        rows.append( ( 'currently shows (turn off to hide): ', self._show ) )
        
        gridbox = ClientGUICommon.WrapInGrid( show_panel, rows )
        
        show_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        rows = []
        
        rows.append( ( 'background colour: ', self._background_colour ) )
        rows.append( ( 'text colour: ', self._text_colour ) )
        
        gridbox = ClientGUICommon.WrapInGrid( edit_panel, rows )
        
        edit_panel.Add( ClientGUICommon.BetterStaticText( edit_panel, 'The colours only work for the thumbnails right now!' ), CC.FLAGS_EXPAND_PERPENDICULAR )
        edit_panel.Add( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        edit_panel.Add( self._namespaces_listbox, CC.FLAGS_EXPAND_BOTH_WAYS )
        edit_panel.Add( ClientGUICommon.WrapInText( self._separator, edit_panel, 'separator' ), CC.FLAGS_EXPAND_PERPENDICULAR )
        
        example_panel.Add( ClientGUICommon.BetterStaticText( example_panel, 'Enter some newline-separated tags here to see what your current object would generate.' ), CC.FLAGS_EXPAND_PERPENDICULAR )
        example_panel.Add( self._example_tags, CC.FLAGS_EXPAND_BOTH_WAYS )
        example_panel.Add( self._test_result, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( show_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( edit_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( example_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        #
        
        self._show.Bind( wx.EVT_CHECKBOX, self.EventChange )
        self._separator.Bind( wx.EVT_TEXT, self.EventChange )
        self._example_tags.Bind( wx.EVT_TEXT, self.EventChange )
        self.Bind( ClientGUIListBoxes.EVT_LIST_BOX, self.EventChange )
        
    
    def _AddNamespaceInfo( self ):
        
        namespace = ''
        prefix = ''
        separator = ', '
        
        namespace_info = ( namespace, prefix, separator )
        
        return self._EditNamespaceInfo( namespace_info )
        
    
    def _ConvertNamespaceToListBoxString( self, namespace_info ):
        
        ( namespace, prefix, separator ) = namespace_info
        
        if namespace == '':
            
            pretty_namespace = 'unnamespaced'
            
        else:
            
            pretty_namespace = namespace
            
        
        pretty_prefix = prefix
        pretty_separator = separator
        
        return pretty_namespace + ' | prefix: "' + pretty_prefix + '" | separator: "' + pretty_separator + '"'
        
    
    def _EditNamespaceInfo( self, namespace_info ):
        
        ( namespace, prefix, separator ) = namespace_info
        
        message = 'Edit namespace.'
        
        with ClientGUIDialogs.DialogTextEntry( self, message, namespace, allow_blank = True ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                namespace = dlg.GetValue()
                
            else:
                
                return ( False, '' )
                
            
        
        message = 'Edit prefix.'
        
        with ClientGUIDialogs.DialogTextEntry( self, message, prefix, allow_blank = True ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                prefix = dlg.GetValue()
                
            else:
                
                return ( False, '' )
                
            
        
        message = 'Edit separator.'
        
        with ClientGUIDialogs.DialogTextEntry( self, message, separator, allow_blank = True ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                separator = dlg.GetValue()
                
                namespace_info = ( namespace, prefix, separator )
                
                return ( True, namespace_info )
                
            else:
                
                return ( False, '' )
                
            
        
    
    def _UpdateTest( self ):
        
        tag_summary_generator = self.GetValue()
        
        self._test_result.SetValue( tag_summary_generator.GenerateExampleSummary() )
        
    
    def EventChange( self, event ):
        
        self._UpdateTest()
        
        event.Skip()
        
    
    def GetValue( self ):
        
        show = self._show.GetValue()
        
        background_colour = self._background_colour.GetValue()
        text_colour = self._text_colour.GetValue()
        namespace_info = self._namespaces_listbox.GetData()
        separator = self._separator.GetValue()
        example_tags = HydrusTags.CleanTags( HydrusText.DeserialiseNewlinedTexts( self._example_tags.GetValue() ) )
        
        return ClientTags.TagSummaryGenerator( background_colour, text_colour, namespace_info, separator, example_tags, show )
        
    
class TagSummaryGeneratorButton( ClientGUICommon.BetterButton ):
    
    def __init__( self, parent, tag_summary_generator ):
        
        label = tag_summary_generator.GenerateExampleSummary()
        
        ClientGUICommon.BetterButton.__init__( self, parent, label, self._Edit )
        
        self._tag_summary_generator = tag_summary_generator
        
    
    def _Edit( self ):
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit tag summary' ) as dlg:
            
            panel = EditTagSummaryGeneratorPanel( dlg, self._tag_summary_generator )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                self._tag_summary_generator = panel.GetValue()
                
                self.SetLabelText( self._tag_summary_generator.GenerateExampleSummary() )
                
            
        
    
    def GetValue( self ):
        
        return self._tag_summary_generator
        
    
class EditURLMatchPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, url_match ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_url_match = url_match
        
        self._name = wx.TextCtrl( self )
        
        self._url_type = ClientGUICommon.BetterChoice( self )
        
        for url_type in ( HC.URL_TYPE_POST, HC.URL_TYPE_GALLERY, HC.URL_TYPE_WATCHABLE, HC.URL_TYPE_FILE ):
            
            self._url_type.Append( HC.url_type_string_lookup[ url_type ], url_type )
            
        
        self._preferred_scheme = ClientGUICommon.BetterChoice( self )
        
        self._preferred_scheme.Append( 'http', 'http' )
        self._preferred_scheme.Append( 'https', 'https' )
        
        self._netloc = wx.TextCtrl( self )
        
        self._match_subdomains = wx.CheckBox( self )
        
        tt = 'Should this class apply to subdomains as well?'
        tt += os.linesep * 2
        tt += 'For instance, if this url class has domain \'example.com\', should it match a url with \'boards.example.com\' or \'artistname.example.com\'?'
        tt += os.linesep * 2
        tt += 'Any subdomain starting with \'www\' is automatically matched, so do not worry about having to account for that.'
        
        self._match_subdomains.SetToolTip( tt )
        
        self._keep_matched_subdomains = wx.CheckBox( self )
        
        tt = 'Should this url keep its matched subdomains when it is normalised?'
        tt += os.linesep * 2
        tt += 'This is typically useful for direct file links that are often served on a numbered CDN subdomain like \'img3.example.com\' but are also valid on the neater main domain.'
        
        self._keep_matched_subdomains.SetToolTip( tt )
        
        self._can_produce_multiple_files = wx.CheckBox( self )
        
        tt = 'If checked, the client will not rely on instances of this URL class to predetermine \'already in db\' or \'previously deleted\' outcomes. This is important for post types like pixiv pages (which can ultimately be manga, and represent many pages) and tweets (which can have multiple images).'
        tt += os.linesep * 2
        tt += 'Most booru-type Post URLs only produce one file per URL and should not have this checked. Checking this avoids some bad logic where the client would falsely think it if it had seen one file at the URL, it had seen them all, but it then means the client has to download those pages\' content again whenever it sees them (so it can check against the direct File URLs, which are always considered one-file each).'
        
        self._can_produce_multiple_files.SetToolTip( tt )
        
        self._should_be_associated_with_files = wx.CheckBox( self )
        
        tt = 'If checked, the client will try to remember this url with any files it ends up importing. It will present this url in \'known urls\' ui across the program.'
        tt += os.linesep * 2
        tt += 'If this URL is a File or Post URL and the client comes across it after having already downloaded it once, it can skip the redundant download since it knows it already has (or has already deleted) the file once before.'
        tt += os.linesep * 2
        tt += 'Turning this on is only useful if the URL is non-ephemeral (i.e. the URL will produce the exact same file(s) in six months\' time). It is usually not appropriate for booru gallery or thread urls, which alter regularly, but is for static Post URLs or some fixed doujin galleries.'
        
        self._should_be_associated_with_files.SetToolTip( tt )
        
        #
        
        path_components_panel = ClientGUICommon.StaticBox( self, 'path components' )
        
        self._path_components = ClientGUIListBoxes.QueueListBox( path_components_panel, 6, self._ConvertPathComponentToString, self._AddPathComponent, self._EditPathComponent )
        
        #
        
        parameters_panel = ClientGUICommon.StaticBox( self, 'parameters' )
        
        parameters_listctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( parameters_panel )
        
        self._parameters = ClientGUIListCtrl.BetterListCtrl( parameters_listctrl_panel, 'url_match_path_components', 5, 45, [ ( 'key', 14 ), ( 'value', -1 ) ], self._ConvertParameterToListCtrlTuples, delete_key_callback = self._DeleteParameters, activation_callback = self._EditParameters )
        
        parameters_listctrl_panel.SetListCtrl( self._parameters )
        
        parameters_listctrl_panel.AddButton( 'add', self._AddParameters )
        parameters_listctrl_panel.AddButton( 'edit', self._EditParameters, enabled_only_on_selection = True )
        parameters_listctrl_panel.AddButton( 'delete', self._DeleteParameters, enabled_only_on_selection = True )
        
        #
        
        self._example_url = wx.TextCtrl( self )
        
        self._example_url_matches = ClientGUICommon.BetterStaticText( self )
        
        self._normalised_url = wx.TextCtrl( self, style = wx.TE_READONLY )
        
        tt = 'The same url can be expressed in different ways. The parameters can be reordered, and descriptive \'sugar\' like "/123456/some-changing-tags-here" can be appended and then altered at a later date. In order to collapse all the different expressions of a url down to a single comparable form, the client will \'normalise\' them based on the essential definitions in their url class. Parameters will be alphebatised and non-defined elements will be removed.'
        tt += os.linesep * 2
        tt += 'All normalisation will switch to the preferred scheme, but the alphabetisation of parameters and stripping out of non-defined elements will only occur if this url is associated with files or uses an API Lookup. (In general, you can define gallery and watchable urls a little more loosely since they generally do not need to be compared, but if you will be saving it with a file or need to perform some regex transformation into an API URL, you\'ll want a rigorously defined url class that will normalise to something reliable and pretty.)'
        
        self._normalised_url.SetToolTip( tt )
        
        ( url_type, preferred_scheme, netloc, match_subdomains, keep_matched_subdomains, path_components, parameters, api_lookup_converter, can_produce_multiple_files, should_be_associated_with_files, example_url ) = url_match.ToTuple()
        
        self._api_lookup_converter = ClientGUIParsing.StringConverterButton( self, api_lookup_converter )
        
        self._api_url = wx.TextCtrl( self, style = wx.TE_READONLY )
        
        #
        
        name = url_match.GetName()
        
        self._name.SetValue( name )
        
        self._url_type.SelectClientData( url_type )
        
        self._preferred_scheme.SelectClientData( preferred_scheme )
        
        self._netloc.SetValue( netloc )
        
        self._match_subdomains.SetValue( match_subdomains )
        self._keep_matched_subdomains.SetValue( keep_matched_subdomains )
        self._can_produce_multiple_files.SetValue( can_produce_multiple_files )
        self._should_be_associated_with_files.SetValue( should_be_associated_with_files )
        
        self._path_components.AddDatas( path_components )
        
        self._parameters.AddDatas( parameters.items() )
        
        self._parameters.Sort()
        
        self._example_url.SetValue( example_url )
        
        example_url_width = ClientGUICommon.ConvertTextToPixelWidth( self._example_url, 75 )
        
        self._example_url.SetMinSize( ( example_url_width, -1 ) )
        
        self._UpdateControls()
        
        #
        
        path_components_panel.Add( self._path_components, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        #
        
        parameters_panel.Add( parameters_listctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        #
        
        rows = []
        
        rows.append( ( 'name: ', self._name ) )
        rows.append( ( 'url type: ', self._url_type ) )
        rows.append( ( 'preferred scheme: ', self._preferred_scheme ) )
        rows.append( ( 'network location: ', self._netloc ) )
        rows.append( ( 'match subdomains?: ', self._match_subdomains ) )
        rows.append( ( 'keep matched subdomains?: ', self._keep_matched_subdomains ) )
        rows.append( ( 'can produce multiple files: ', self._can_produce_multiple_files ) )
        rows.append( ( 'should associate a \'known url\' with resulting files: ', self._should_be_associated_with_files ) )
        
        gridbox_1 = ClientGUICommon.WrapInGrid( self, rows )
        
        rows = []
        
        rows.append( ( 'example url: ', self._example_url ) )
        rows.append( ( 'normalised url: ', self._normalised_url ) )
        rows.append( ( 'optional api url converter: ', self._api_lookup_converter ) )
        rows.append( ( 'api url: ', self._api_url ) )
        
        gridbox_2 = ClientGUICommon.WrapInGrid( self, rows )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( gridbox_1, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( path_components_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( parameters_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        vbox.Add( self._example_url_matches, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( gridbox_2, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
        #
        
        self._preferred_scheme.Bind( wx.EVT_CHOICE, self.EventUpdate )
        self._netloc.Bind( wx.EVT_TEXT, self.EventUpdate )
        self.Bind( wx.EVT_CHECKBOX, self.EventUpdate )
        self._example_url.Bind( wx.EVT_TEXT, self.EventUpdate )
        self.Bind( ClientGUIListBoxes.EVT_LIST_BOX, self.EventUpdate )
        self._url_type.Bind( wx.EVT_CHOICE, self.EventURLTypeUpdate )
        self._api_lookup_converter.Bind( ClientGUIParsing.EVT_STRING_CONVERTER, self.EventUpdate )
        self._should_be_associated_with_files.Bind( wx.EVT_CHECKBOX, self.EventAssociationUpdate )
        
    
    def _AddParameters( self ):
        
        with ClientGUIDialogs.DialogTextEntry( self, 'edit the key', default = 'key', allow_blank = False ) as dlg:
            
            if dlg.ShowModal() == wx.ID_OK:
                
                key = dlg.GetValue()
                
            else:
                
                return
                
            
        
        existing_keys = self._GetExistingKeys()
        
        if key in existing_keys:
            
            wx.MessageBox( 'That key already exists!' )
            
            return
            
        
        string_match = ClientParsing.StringMatch()
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit value' ) as dlg:
            
            panel = ClientGUIParsing.EditStringMatchPanel( dlg, string_match )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                string_match = panel.GetValue()
                
            else:
                
                return
                
            
        
        data = ( key, string_match )
        
        self._parameters.AddDatas( ( data, ) )
        
        self._parameters.Sort()
        
        self._UpdateControls()
        
    
    def _AddPathComponent( self ):
        
        string_match = ClientParsing.StringMatch()
        
        return self._EditPathComponent( string_match )
        
    
    def _ConvertParameterToListCtrlTuples( self, data ):
        
        ( key, string_match ) = data
        
        pretty_key = key
        pretty_string_match = string_match.ToUnicode()
        
        sort_key = pretty_key
        sort_string_match = pretty_string_match
        
        display_tuple = ( pretty_key, pretty_string_match )
        sort_tuple = ( sort_key, sort_string_match )
        
        return ( display_tuple, sort_tuple )
        
    
    def _ConvertPathComponentToString( self, path_component ):
        
        return path_component.ToUnicode()
        
    
    def _DeleteParameters( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._parameters.DeleteSelected()
                
            
        
        self._UpdateControls()
        
    
    def _EditParameters( self ):
        
        selected_params = self._parameters.GetData( only_selected = True )
        
        for parameter in selected_params:
            
            ( original_key, original_string_match ) = parameter
            
            with ClientGUIDialogs.DialogTextEntry( self, 'edit the key', default = original_key, allow_blank = False ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    key = dlg.GetValue()
                    
                else:
                    
                    return
                    
                
            
            if key != original_key:
                
                existing_keys = self._GetExistingKeys()
                
                if key in existing_keys:
                    
                    wx.MessageBox( 'That key already exists!' )
                    
                    return
                    
                
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit value' ) as dlg:
                
                panel = ClientGUIParsing.EditStringMatchPanel( dlg, original_string_match )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    string_match = panel.GetValue()
                    
                else:
                    
                    return
                    
                
            
            self._parameters.DeleteDatas( ( parameter, ) )
            
            new_parameter = ( key, string_match )
            
            self._parameters.AddDatas( ( new_parameter, ) )
            
        
        self._parameters.Sort()
        
        self._UpdateControls()
        
    
    def _EditPathComponent( self, string_match ):
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit path component' ) as dlg:
            
            panel = ClientGUIParsing.EditStringMatchPanel( dlg, string_match )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                new_string_match = panel.GetValue()
                
                return ( True, new_string_match )
                
            else:
                
                return ( False, None )
                
            
        
    
    def _GetExistingKeys( self ):
        
        params = self._parameters.GetData()
        
        keys = { key for ( key, string_match ) in params }
        
        return keys
        
    
    def _GetValue( self ):
        
        url_match_key = self._original_url_match.GetMatchKey()
        name = self._name.GetValue()
        url_type = self._url_type.GetChoice()
        preferred_scheme = self._preferred_scheme.GetChoice()
        netloc = self._netloc.GetValue()
        match_subdomains = self._match_subdomains.GetValue()
        keep_matched_subdomains = self._keep_matched_subdomains.GetValue()
        can_produce_multiple_files = self._can_produce_multiple_files.GetValue()
        should_be_associated_with_files = self._should_be_associated_with_files.GetValue()
        path_components = self._path_components.GetData()
        parameters = dict( self._parameters.GetData() )
        api_lookup_converter = self._api_lookup_converter.GetValue()
        example_url = self._example_url.GetValue()
        
        url_match = ClientNetworkingDomain.URLMatch( name, url_match_key = url_match_key, url_type = url_type, preferred_scheme = preferred_scheme, netloc = netloc, match_subdomains = match_subdomains, keep_matched_subdomains = keep_matched_subdomains, path_components = path_components, parameters = parameters, api_lookup_converter = api_lookup_converter, can_produce_multiple_files = can_produce_multiple_files, should_be_associated_with_files = should_be_associated_with_files, example_url = example_url )
        
        return url_match
        
    
    def _UpdateControls( self ):
        
        url_match = self._GetValue()
        
        url_type = url_match.GetURLType()
        
        if url_type == HC.URL_TYPE_POST:
            
            self._can_produce_multiple_files.Enable()
            
        else:
            
            self._can_produce_multiple_files.Disable()
            
        
        if url_match.NormalisationIsAppropriate():
            
            if self._match_subdomains.GetValue():
                
                self._keep_matched_subdomains.Enable()
                
            else:
                
                self._keep_matched_subdomains.SetValue( False )
                self._keep_matched_subdomains.Disable()
                
            
        else:
            
            self._keep_matched_subdomains.Disable()
            
        
        try:
            
            example_url = self._example_url.GetValue()
            
            self._api_lookup_converter.SetExampleString( example_url )
            
            url_match.Test( example_url )
            
            self._example_url_matches.SetLabelText( 'Example matches ok!' )
            self._example_url_matches.SetForegroundColour( ( 0, 128, 0 ) )
            
            normalised = url_match.Normalise( example_url )
            
            self._normalised_url.SetValue( normalised )
            
            try:
                
                if url_match.UsesAPIURL():
                    
                    api_lookup_url = url_match.GetAPIURL( normalised )
                    
                else:
                    
                    api_lookup_url = 'none set'
                    
                
                self._api_url.SetValue( api_lookup_url )
                
            except HydrusExceptions.StringConvertException as e:
                
                reason = HydrusData.ToUnicode( e )
                
                self._api_url.SetValue( 'Could not convert - ' + reason )
                
            
        except HydrusExceptions.URLMatchException as e:
            
            reason = HydrusData.ToUnicode( e )
            
            self._example_url_matches.SetLabelText( 'Example does not match - ' + reason )
            self._example_url_matches.SetForegroundColour( ( 128, 0, 0 ) )
            
            self._normalised_url.SetValue( '' )
            self._api_url.SetValue( '' )
            
        
    
    def EventAssociationUpdate( self, event ):
        
        if self._should_be_associated_with_files.GetValue() == True:
            
            if self._url_type.GetChoice() in ( HC.URL_TYPE_GALLERY, HC.URL_TYPE_WATCHABLE ):
                
                message = 'Please note that it is only appropriate to associate a Gallery or Watchable URL with a file if that URL is non-ephemeral. It is only appropriate if the exact same URL will definitely give the same files in six months\' time (like a fixed doujin chapter gallery).'
                message += os.linesep * 2
                message += 'If you are not sure what this means, turn this back off.'
                
                wx.MessageBox( message )
                
            
        else:
            
            if self._url_type.GetChoice() in ( HC.URL_TYPE_FILE, HC.URL_TYPE_POST ):
                
                message = 'Hydrus uses these file associations to make sure not to re-download the same file when it comes across the same URL in future. It is only appropriate to not associate a file or post url with a file if that url is particularly ephemeral, such as if the URL includes a non-removable random key that becomes invalid after a few minutes.'
                message += os.linesep * 2
                message += 'If you are not sure what this means, turn this back on.'
                
                wx.MessageBox( message )
                
            
        
        event.Skip()
        
    
    def EventUpdate( self, event ):
        
        self._UpdateControls()
        
    
    def EventURLTypeUpdate( self, event ):
        
        url_type = self._url_type.GetChoice()
        
        if url_type in ( HC.URL_TYPE_FILE, HC.URL_TYPE_POST ):
            
            self._should_be_associated_with_files.SetValue( True )
            
        else:
            
            self._should_be_associated_with_files.SetValue( False )
            
        
        self._UpdateControls()
        
    
    def GetValue( self ):
        
        url_match = self._GetValue()
        
        try:
            
            url_match.Test( self._example_url.GetValue() )
            
        except HydrusExceptions.URLMatchException:
            
            raise HydrusExceptions.VetoException( 'Please enter an example url that matches the given rules!' )
            
        
        return url_match
        
    
class EditURLMatchesPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, url_matches ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        menu_items = []
        
        page_func = HydrusData.Call( ClientPaths.LaunchPathInWebBrowser, os.path.join( HC.HELP_DIR, 'downloader_url_classes.html' ) )
        
        menu_items.append( ( 'normal', 'open the url classes help', 'Open the help page for url classes in your web browesr.', page_func ) )
        
        help_button = ClientGUICommon.MenuBitmapButton( self, CC.GlobalBMPs.help, menu_items )
        
        help_hbox = ClientGUICommon.WrapInText( help_button, self, 'help for this panel -->', wx.Colour( 0, 0, 255 ) )
        
        self._url_class_checker = wx.TextCtrl( self )
        self._url_class_checker.Bind( wx.EVT_TEXT, self.EventURLClassCheckerText )
        
        self._url_class_checker_st = ClientGUICommon.BetterStaticText( self )
        
        self._list_ctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self )
        
        self._list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._list_ctrl_panel, 'url_matches', 15, 40, [ ( 'name', 36 ), ( 'type', 20 ), ( 'example (normalised) url', -1 ) ], self._ConvertDataToListCtrlTuples, delete_key_callback = self._Delete, activation_callback = self._Edit )
        
        self._list_ctrl_panel.SetListCtrl( self._list_ctrl )
        
        self._list_ctrl_panel.AddButton( 'add', self._Add )
        self._list_ctrl_panel.AddButton( 'edit', self._Edit, enabled_only_on_selection = True )
        self._list_ctrl_panel.AddButton( 'delete', self._Delete, enabled_only_on_selection = True )
        self._list_ctrl_panel.AddSeparator()
        self._list_ctrl_panel.AddImportExportButtons( ( ClientNetworkingDomain.URLMatch, ), self._AddURLMatch )
        self._list_ctrl_panel.AddSeparator()
        self._list_ctrl_panel.AddDefaultsButton( ClientDefaults.GetDefaultURLMatches, self._AddURLMatch )
        
        #
        
        self._list_ctrl.AddDatas( url_matches )
        
        self._list_ctrl.Sort( 0 )
        
        #
        
        url_hbox = wx.BoxSizer( wx.HORIZONTAL )
        
        url_hbox.Add( self._url_class_checker, CC.FLAGS_EXPAND_BOTH_WAYS )
        url_hbox.Add( self._url_class_checker_st, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( help_hbox, CC.FLAGS_BUTTON_SIZER )
        vbox.Add( url_hbox, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.Add( self._list_ctrl_panel, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        #
        
        self._UpdateURLClassCheckerText()
        
    
    def _Add( self ):
        
        url_match = ClientNetworkingDomain.URLMatch( 'new url class' )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit url class' ) as dlg:
            
            panel = EditURLMatchPanel( dlg, url_match )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                url_match = panel.GetValue()
                
                self._AddURLMatch( url_match )
                
                self._list_ctrl.Sort()
                
            
        
    
    def _AddURLMatch( self, url_match ):
        
        HydrusSerialisable.SetNonDupeName( url_match, self._GetExistingNames() )
        
        url_match.RegenMatchKey()
        
        self._list_ctrl.AddDatas( ( url_match, ) )
        
    
    def _ConvertDataToListCtrlTuples( self, url_match ):
        
        name = url_match.GetName()
        url_type = url_match.GetURLType()
        example_url = url_match.Normalise( url_match.GetExampleURL() )
        
        pretty_name = name
        pretty_url_type = HC.url_type_string_lookup[ url_type ]
        pretty_example_url = example_url
        
        display_tuple = ( pretty_name, pretty_url_type, pretty_example_url )
        sort_tuple = ( name, url_type, example_url )
        
        return ( display_tuple, sort_tuple )
        
    
    def _Delete( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Remove all selected?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._list_ctrl.DeleteSelected()
                
            
        
    
    def _Edit( self ):
        
        for url_match in self._list_ctrl.GetData( only_selected = True ):
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit url class' ) as dlg:
                
                panel = EditURLMatchPanel( dlg, url_match )
                
                dlg.SetPanel( panel )
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    self._list_ctrl.DeleteDatas( ( url_match, ) )
                    
                    url_match = panel.GetValue()
                    
                    HydrusSerialisable.SetNonDupeName( url_match, self._GetExistingNames() )
                    
                    self._list_ctrl.AddDatas( ( url_match, ) )
                    
                else:
                    
                    break
                    
                
            
        
        self._list_ctrl.Sort()
        
    
    def _GetExistingNames( self ):
        
        url_matches = self._list_ctrl.GetData()
        
        names = { url_match.GetName() for url_match in url_matches }
        
        return names
        
    
    def _UpdateURLClassCheckerText( self ):
        
        url = self._url_class_checker.GetValue()
        
        if url == '':
            
            text = '<-- Enter a URL here to see which url class it currently matches!'
            
        else:
            
            url_matches = self.GetValue()
            
            domain_manager = ClientNetworkingDomain.NetworkDomainManager()
            
            domain_manager.Initialise()
            
            domain_manager.SetURLMatches( url_matches )
            
            try:
                
                url_match = domain_manager.GetURLMatch( url )
                
                if url_match is None:
                    
                    text = 'No match!'
                    
                else:
                    
                    text = 'Matches "' + url_match.GetName() + '"'
                    
                
            except HydrusExceptions.URLMatchException as e:
                
                text = HydrusData.ToUnicode( e )
                
            
        
        self._url_class_checker_st.SetLabelText( text )
        
    
    def EventURLClassCheckerText( self, event ):
        
        self._UpdateURLClassCheckerText()
        
    
    def GetValue( self ):
        
        url_matches = self._list_ctrl.GetData()
        
        return url_matches
        
    
class EditURLMatchLinksPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, network_engine, url_matches, parsers, url_match_keys_to_display, url_match_keys_to_parser_keys ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._url_matches = url_matches
        self._url_match_keys_to_url_matches = { url_match.GetMatchKey() : url_match for url_match in self._url_matches }
        
        self._parsers = parsers
        self._parser_keys_to_parsers = { parser.GetParserKey() : parser for parser in self._parsers }
        
        self._network_engine = network_engine
        
        #
        
        self._notebook = wx.Notebook( self )
        
        #
        
        self._display_list_ctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self._notebook )
        
        self._display_list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._display_list_ctrl_panel, 'url_match_keys_to_display', 15, 36, [ ( 'url class', -1 ), ( 'url type', 20 ), ( 'display on media viewer?', 36 ) ], self._ConvertDisplayDataToListCtrlTuples, activation_callback = self._EditDisplay )
        
        self._display_list_ctrl_panel.SetListCtrl( self._display_list_ctrl )
        
        self._display_list_ctrl_panel.AddButton( 'edit', self._EditDisplay, enabled_only_on_selection = True )
        
        #
        
        self._api_pairs_list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._notebook, 'url_match_api_pairs', 10, 36, [ ( 'url class', -1 ), ( 'api url class', 36 ) ], self._ConvertAPIPairDataToListCtrlTuples )
        
        #
        
        self._parser_list_ctrl_panel = ClientGUIListCtrl.BetterListCtrlPanel( self._notebook )
        
        self._parser_list_ctrl = ClientGUIListCtrl.BetterListCtrl( self._parser_list_ctrl_panel, 'url_match_keys_to_parser_keys', 24, 36, [ ( 'url class', -1 ), ( 'url type', 20 ), ( 'parser', 36 ) ], self._ConvertParserDataToListCtrlTuples, activation_callback = self._EditParser )
        
        self._parser_list_ctrl_panel.SetListCtrl( self._parser_list_ctrl )
        
        self._parser_list_ctrl_panel.AddButton( 'edit', self._EditParser, enabled_only_on_selection = True )
        self._parser_list_ctrl_panel.AddButton( 'clear', self._ClearParser, enabled_check_func = self._LinksOnCurrentSelection )
        self._parser_list_ctrl_panel.AddButton( 'try to fill in gaps based on example urls', self._TryToLinkUrlMatchesAndParsers, enabled_check_func = self._GapsExist )
        
        #
        
        listctrl_data = []
        
        for url_match in url_matches:
            
            url_match_key = url_match.GetMatchKey()
            
            display = url_match_key in url_match_keys_to_display
            
            listctrl_data.append( ( url_match_key, display ) )
            
        
        self._display_list_ctrl.AddDatas( listctrl_data )
        
        self._display_list_ctrl.Sort( 1 )
        
        #
        
        api_pairs = ClientNetworkingDomain.ConvertURLMatchesIntoAPIPairs( url_matches )
        
        self._api_pairs_list_ctrl.AddDatas( api_pairs )
        
        # anything that goes to an api url will be parsed by that api's parser--it can't have its own
        api_pair_unparsable_url_matches = set()
        
        for ( a, b ) in api_pairs:
            
            api_pair_unparsable_url_matches.add( a )
            
        
        #
        
        listctrl_data = []
        
        for url_match in url_matches:
            
            if not url_match.IsParsable() or url_match in api_pair_unparsable_url_matches:
                
                continue
                
            
            if not ( url_match.IsWatchableURL() or url_match.IsPostURL() ):
                
                continue
                
            
            url_match_key = url_match.GetMatchKey()
            
            if url_match_key in url_match_keys_to_parser_keys:
                
                parser_key = url_match_keys_to_parser_keys[ url_match_key ]
                
            else:
                
                parser_key = None
                
            
            listctrl_data.append( ( url_match_key, parser_key ) )
            
        
        self._parser_list_ctrl.AddDatas( listctrl_data )
        
        self._parser_list_ctrl.Sort( 1 )
        
        #
        
        self._notebook.AddPage( self._parser_list_ctrl_panel, 'parser links' )
        self._notebook.AddPage( self._api_pairs_list_ctrl, 'api link review' )
        self._notebook.AddPage( self._display_list_ctrl_panel, 'media viewer display' )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.Add( self._notebook, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
    
    def _ClearParser( self ):
        
        with ClientGUIDialogs.DialogYesNo( self, 'Clear all the selected linked parsers?' ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                for data in self._parser_list_ctrl.GetData( only_selected = True ):
                    
                    self._parser_list_ctrl.DeleteDatas( ( data, ) )
                    
                    ( url_match_key, parser_key ) = data
                    
                    new_data = ( url_match_key, None )
                    
                    self._parser_list_ctrl.AddDatas( ( new_data, ) )
                    
                
                self._parser_list_ctrl.Sort()
                
            
        
    
    def _ConvertAPIPairDataToListCtrlTuples( self, data ):
        
        ( a, b ) = data
        
        a_name = a.GetName()
        b_name = b.GetName()
        
        pretty_a_name = a_name
        pretty_b_name = b_name
        
        display_tuple = ( pretty_a_name, pretty_b_name )
        sort_tuple = ( a_name, b_name )
        
        return ( display_tuple, sort_tuple )
        
    
    def _ConvertDisplayDataToListCtrlTuples( self, data ):
        
        ( url_match_key, display ) = data
        
        url_match = self._url_match_keys_to_url_matches[ url_match_key ]
        
        url_match_name = url_match.GetName()
        url_type = url_match.GetURLType()
        
        pretty_name = url_match_name
        pretty_url_type = HC.url_type_string_lookup[ url_type ]
        
        if display:
            
            pretty_display = 'yes'
            
        else:
            
            pretty_display = 'no'
            
        
        display_tuple = ( pretty_name, pretty_url_type, pretty_display )
        sort_tuple = ( url_match_name, pretty_url_type, display )
        
        return ( display_tuple, sort_tuple )
        
    
    def _ConvertParserDataToListCtrlTuples( self, data ):
        
        ( url_match_key, parser_key ) = data
        
        url_match = self._url_match_keys_to_url_matches[ url_match_key ]
        
        url_match_name = url_match.GetName()
        
        url_type = url_match.GetURLType()
        
        if parser_key is None:
            
            parser_name = ''
            
        else:
            
            parser = self._parser_keys_to_parsers[ parser_key ]
            
            parser_name = parser.GetName()
            
        
        pretty_url_match_name = url_match_name
        
        pretty_url_type = HC.url_type_string_lookup[ url_type ]
        
        pretty_parser_name = parser_name
        
        display_tuple = ( pretty_url_match_name, pretty_url_type, pretty_parser_name )
        sort_tuple = ( url_match_name, pretty_url_type, parser_name )
        
        return ( display_tuple, sort_tuple )
        
    
    def _EditDisplay( self ):
        
        for data in self._display_list_ctrl.GetData( only_selected = True ):
            
            ( url_match_key, display ) = data
            
            url_match_name = self._url_match_keys_to_url_matches[ url_match_key ].GetName()
            
            message = 'Show ' + url_match_name + ' in the media viewer?'
            
            with ClientGUIDialogs.DialogYesNo( self, message, title = 'Show in the media viewer?' ) as dlg:
                
                result = dlg.ShowModal()
                
                if result in ( wx.ID_YES, wx.ID_NO ):
                    
                    display = result == wx.ID_YES
                    
                    self._display_list_ctrl.DeleteDatas( ( data, ) )
                    
                    new_data = ( url_match_key, display )
                    
                    self._display_list_ctrl.AddDatas( ( new_data, ) )
                    
                else:
                    
                    break
                    
                
            
        
        self._display_list_ctrl.Sort()
        
    
    def _EditParser( self ):
        
        if len( self._parsers ) == 0:
            
            wx.MessageBox( 'Unfortunately, you do not have any parsers, so none can be linked to your url classes. Please create some!' )
            
            return
            
        
        for data in self._parser_list_ctrl.GetData( only_selected = True ):
            
            ( url_match_key, parser_key ) = data
            
            url_match = self._url_match_keys_to_url_matches[ url_match_key ]
            
            choice_tuples = [ ( parser.GetName(), parser ) for parser in self._parsers ]
            
            with ClientGUIDialogs.DialogSelectFromList( self, 'select parser for ' + url_match.GetName(), choice_tuples ) as dlg:
                
                if dlg.ShowModal() == wx.ID_OK:
                    
                    parser = dlg.GetChoice()
                    
                    self._parser_list_ctrl.DeleteDatas( ( data, ) )
                    
                    new_data = ( url_match_key, parser.GetParserKey() )
                    
                    self._parser_list_ctrl.AddDatas( ( new_data, ) )
                    
                else:
                    
                    break
                    
                
            
        
        self._parser_list_ctrl.Sort()
        
    
    def _GapsExist( self ):
        
        return None in ( parser_key for ( url_match_key, parser_key ) in self._parser_list_ctrl.GetData() )
        
    
    def _LinksOnCurrentSelection( self ):
        
        non_none_parser_keys = [ parser_key for ( url_match_key, parser_key ) in self._parser_list_ctrl.GetData( only_selected = True ) if parser_key is not None ]
        
        return len( non_none_parser_keys ) > 0
        
    
    def _TryToLinkUrlMatchesAndParsers( self ):
        
        existing_url_match_keys_to_parser_keys = { url_match_key : parser_key for ( url_match_key, parser_key ) in self._parser_list_ctrl.GetData() if parser_key is not None }
        
        new_url_match_keys_to_parser_keys = ClientNetworkingDomain.NetworkDomainManager.STATICLinkURLMatchesAndParsers( self._url_matches, self._parsers, existing_url_match_keys_to_parser_keys )
        
        if len( new_url_match_keys_to_parser_keys ) > 0:
            
            removees = []
            
            for row in self._parser_list_ctrl.GetData():
                
                ( url_match_key, parser_key ) = row
                
                if url_match_key in new_url_match_keys_to_parser_keys:
                    
                    removees.append( row )
                    
                
            
            self._parser_list_ctrl.DeleteDatas( removees )
            
            self._parser_list_ctrl.AddDatas( new_url_match_keys_to_parser_keys.items() )
            
            self._parser_list_ctrl.Sort()
            
        
    
    def GetValue( self ):
        
        url_match_keys_to_display = { url_match_key for ( url_match_key, display ) in self._display_list_ctrl.GetData() if display }
        url_match_keys_to_parser_keys = { url_match_key : parser_key for ( url_match_key, parser_key ) in self._parser_list_ctrl.GetData() if parser_key is not None }
        
        return ( url_match_keys_to_display, url_match_keys_to_parser_keys )
        
    
