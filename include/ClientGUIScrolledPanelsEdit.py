import ClientConstants as CC
import ClientDefaults
import ClientDownloading
import ClientImporting
import ClientGUICollapsible
import ClientGUICommon
import ClientGUIDialogs
import ClientGUIScrolledPanels
import ClientGUITopLevelWindows
import HydrusConstants as HC
import HydrusData
import HydrusGlobals
import wx

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
        
        vbox.AddF( wx.StaticText( self, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._remember_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._remember_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._last_size, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._last_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_gravity_x, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_gravity_y, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._default_position, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._maximised, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._fullscreen, CC.FLAGS_EXPAND_PERPENDICULAR )
        
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
            
            if action != CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW:
                
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
            
            if scale_action != CC.MEDIA_VIEWER_SCALE_100:
                
                self._media_scale_down.Append( text, scale_action )
                self._preview_scale_down.Append( text, scale_action )
                
            
        
        self._exact_zooms_only = wx.CheckBox( self, label = 'only permit half and double zooms' )
        self._exact_zooms_only.SetToolTipString( 'This limits zooms to 25%, 50%, 100%, 200%, 400%, and so on. It makes for fast resize and is useful for files that often have flat colours and hard edges, which often scale badly otherwise. The \'canvas fit\' zoom will still be inserted.' )
        
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
        
        vbox.AddF( wx.StaticText( self, label = text ), CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( ClientGUICommon.WrapInText( self._media_show_action, self, 'media viewer show action:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.AddF( ClientGUICommon.WrapInText( self._preview_show_action, self, 'preview show action:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
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
            
            vbox.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
            vbox.AddF( self._exact_zooms_only, CC.FLAGS_EXPAND_PERPENDICULAR )
            
            vbox.AddF( wx.StaticText( self, label = 'Nearest neighbour is fast and ugly, 8x8 lanczos and area resampling are slower but beautiful.' ), CC.FLAGS_VCENTER )
            
            vbox.AddF( ClientGUICommon.WrapInText( self._scale_up_quality, self, '>100% (interpolation) quality:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            vbox.AddF( ClientGUICommon.WrapInText( self._scale_down_quality, self, '<100% (decimation) quality:' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
            
        
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
        
    
class EditSeedCachePanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, controller, seed_cache ):
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._controller = controller
        self._seed_cache = seed_cache
        
        self._text = wx.StaticText( self, label = 'initialising' )
        self._seed_cache_control = ClientGUICommon.SeedCacheControl( self, self._seed_cache )
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( self._text, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._seed_cache_control, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.SetSizer( vbox )
        
        self._controller.sub( self, 'NotifySeedUpdated', 'seed_cache_seed_updated' )
        
        wx.CallAfter( self._UpdateText )
        
    
    def _UpdateText( self ):
        
        ( status, ( total_processed, total ) ) = self._seed_cache.GetStatus()
        
        self._text.SetLabelText( status )
        
        self.Layout()
        
    
    def GetValue( self ):
        
        return self._seed_cache
        
    
    def NotifySeedUpdated( self, seed ):
        
        self._UpdateText()
        
    
class EditSubscriptionPanel( ClientGUIScrolledPanels.EditPanel ):
    
    def __init__( self, parent, subscription ):
        
        subscription = subscription.Duplicate()
        
        ClientGUIScrolledPanels.EditPanel.__init__( self, parent )
        
        self._original_subscription = subscription
        
        #
        
        self._name = wx.TextCtrl( self )
        
        #
        
        self._info_panel = ClientGUICommon.StaticBox( self, 'info' )
        
        self._last_checked_st = wx.StaticText( self._info_panel )
        self._next_check_st = wx.StaticText( self._info_panel )
        self._seed_info_st = wx.StaticText( self._info_panel )
        
        #
        
        self._query_panel = ClientGUICommon.StaticBox( self, 'site and query' )
        
        self._site_type = ClientGUICommon.BetterChoice( self._query_panel )
        
        site_types = []
        site_types.append( HC.SITE_TYPE_BOORU )
        site_types.append( HC.SITE_TYPE_DEVIANT_ART )
        site_types.append( HC.SITE_TYPE_HENTAI_FOUNDRY_ARTIST )
        site_types.append( HC.SITE_TYPE_HENTAI_FOUNDRY_TAGS )
        site_types.append( HC.SITE_TYPE_NEWGROUNDS )
        site_types.append( HC.SITE_TYPE_PIXIV_ARTIST_ID )
        site_types.append( HC.SITE_TYPE_PIXIV_TAG )
        site_types.append( HC.SITE_TYPE_TUMBLR )
        
        for site_type in site_types:
            
            self._site_type.Append( HC.site_type_string_lookup[ site_type ], site_type )
            
        
        self._site_type.Bind( wx.EVT_CHOICE, self.EventSiteChanged )
        
        self._query = wx.TextCtrl( self._query_panel )
        
        self._booru_selector = wx.ListBox( self._query_panel )
        self._booru_selector.Bind( wx.EVT_LISTBOX, self.EventBooruSelected )
        
        self._period = ClientGUICommon.TimeDeltaButton( self._query_panel, min = 3600 * 4, days = True, hours = True )
        self._period.Bind( ClientGUICommon.EVT_TIME_DELTA, self.EventPeriodChanged )
        
        #
        
        self._options_panel = ClientGUICommon.StaticBox( self, 'options' )
        
        self._get_tags_if_redundant = wx.CheckBox( self._options_panel )
        
        self._initial_file_limit = ClientGUICommon.NoneableSpinCtrl( self._options_panel, '', none_phrase = 'get everything', min = 1, max = 1000000 )
        self._initial_file_limit.SetToolTipString( 'If set, the first sync will add no more than this many files. Otherwise, it will get everything the gallery has.' )
        
        self._periodic_file_limit = ClientGUICommon.NoneableSpinCtrl( self._options_panel, '', none_phrase = 'get everything', min = 1, max = 1000000 )
        self._periodic_file_limit.SetToolTipString( 'If set, normal syncs will add no more than this many files. Otherwise, they will get everything up until they find a file they have seen before.' )
        
        #
        
        self._control_panel = ClientGUICommon.StaticBox( self, 'control' )
        
        self._paused = wx.CheckBox( self._control_panel )
        
        self._seed_cache_button = wx.BitmapButton( self._control_panel, bitmap = CC.GlobalBMPs.seed_cache )
        self._seed_cache_button.Bind( wx.EVT_BUTTON, self.EventSeedCache )
        self._seed_cache_button.SetToolTipString( 'open detailed url cache status' )
        
        self._retry_failed = ClientGUICommon.BetterButton( self._control_panel, 'retry failed', self.RetryFailed )
        
        self._check_now_button = ClientGUICommon.BetterButton( self._control_panel, 'force check on dialog ok', self.CheckNow )
        
        self._reset_cache_button = ClientGUICommon.BetterButton( self._control_panel, 'reset url cache', self.ResetCache )
        
        #
        
        self._import_tag_options = ClientGUICollapsible.CollapsibleOptionsTags( self )
        
        self._import_file_options = ClientGUICollapsible.CollapsibleOptionsImportFiles( self )
        
        #
        
        name = subscription.GetName()
        
        self._name.SetValue( name )
        
        ( gallery_identifier, gallery_stream_identifiers, query, period, get_tags_if_redundant, initial_file_limit, periodic_file_limit, paused, import_file_options, import_tag_options, self._last_checked, self._last_error, self._check_now, self._seed_cache ) = subscription.ToTuple()
        
        site_type = gallery_identifier.GetSiteType()
        
        self._site_type.SelectClientData( site_type )
        
        self._PresentForSiteType()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            booru_name = gallery_identifier.GetAdditionalInfo()
            
            index = self._booru_selector.FindString( booru_name )
            
            if index != wx.NOT_FOUND:
                
                self._booru_selector.Select( index )
                
            
        
        # set gallery_stream_identifiers selection here--some kind of list of checkboxes or whatever
        
        self._query.SetValue( query )
        
        self._period.SetValue( period )
        
        self._get_tags_if_redundant.SetValue( get_tags_if_redundant )
        self._initial_file_limit.SetValue( initial_file_limit )
        self._periodic_file_limit.SetValue( periodic_file_limit )
        
        self._paused.SetValue( paused )
        
        self._import_file_options.SetOptions( import_file_options )
        
        self._import_tag_options.SetOptions( import_tag_options )
        
        if self._last_checked == 0:
            
            self._reset_cache_button.Disable()
            
        
        if self._check_now:
            
            self._check_now_button.Disable()
            
        
        self._UpdateCommandButtons()
        self._UpdateLastNextCheck()
        self._UpdateSeedInfo()
        
        #
        
        self._info_panel.AddF( self._last_checked_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._info_panel.AddF( self._next_check_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._info_panel.AddF( self._seed_info_st, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'search text: ', self._query ) )
        rows.append( ( 'check for new files every: ', self._period ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._query_panel, rows )
        
        self._query_panel.AddF( self._site_type, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._query_panel.AddF( self._booru_selector, CC.FLAGS_EXPAND_PERPENDICULAR )
        self._query_panel.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        rows = []
        
        rows.append( ( 'get tags even if new file is already in db: ', self._get_tags_if_redundant ) )
        rows.append( ( 'on first check, get at most this many files: ', self._initial_file_limit ) )
        rows.append( ( 'on normal checks, get at most this many newer files: ', self._periodic_file_limit ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._options_panel, rows )
        
        self._options_panel.AddF( gridbox, CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        
        #
        
        self._control_panel.AddF( self._seed_cache_button, CC.FLAGS_LONE_BUTTON )
        
        rows = []
        
        rows.append( ( 'currently paused: ', self._paused ) )
        
        gridbox = ClientGUICommon.WrapInGrid( self._control_panel, rows )
        
        self._control_panel.AddF( gridbox, CC.FLAGS_LONE_BUTTON )
        self._control_panel.AddF( self._retry_failed, CC.FLAGS_LONE_BUTTON )
        self._control_panel.AddF( self._check_now_button, CC.FLAGS_LONE_BUTTON )
        self._control_panel.AddF( self._reset_cache_button, CC.FLAGS_LONE_BUTTON )
        
        #
        
        vbox = wx.BoxSizer( wx.VERTICAL )
        
        vbox.AddF( ClientGUICommon.WrapInText( self._name, self, 'name: ' ), CC.FLAGS_EXPAND_SIZER_PERPENDICULAR )
        vbox.AddF( self._info_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._query_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._options_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._control_panel, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._import_tag_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        vbox.AddF( self._import_file_options, CC.FLAGS_EXPAND_PERPENDICULAR )
        
        self.SetSizer( vbox )
        
    
    def _ConfigureImportTagOptions( self ):
        
        gallery_identifier = self._GetGalleryIdentifier()
        
        ( namespaces, search_value ) = ClientDefaults.GetDefaultNamespacesAndSearchValue( gallery_identifier )
        
        new_options = HydrusGlobals.client_controller.GetNewOptions()
        
        import_tag_options = new_options.GetDefaultImportTagOptions( gallery_identifier )
        
        if gallery_identifier == self._original_subscription.GetGalleryIdentifier():
            
            search_value = self._original_subscription.GetQuery()
            import_tag_options = self._original_subscription.GetImportTagOptions()
            
        
        self._query.SetValue( search_value )
        self._import_tag_options.SetNamespaces( namespaces )
        self._import_tag_options.SetOptions( import_tag_options )
        
    
    def _GetGalleryIdentifier( self ):
        
        site_type = self._site_type.GetChoice()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            booru_name = self._booru_selector.GetStringSelection()
            
            gallery_identifier = ClientDownloading.GalleryIdentifier( site_type, additional_info = booru_name )
            
        else:
            
            gallery_identifier = ClientDownloading.GalleryIdentifier( site_type )
            
        
        return gallery_identifier
        
    
    def _UpdateCommandButtons( self ):
        
        on_initial_sync = self._last_checked == 0
        no_failures = self._seed_cache.GetSeedCount( CC.STATUS_FAILED ) == 0
        
        can_check = not ( self._check_now or on_initial_sync )
        
        if no_failures:
            
            self._retry_failed.Disable()
            
        else:
            
            self._retry_failed.Enable()
            
        
        if can_check:
            
            self._check_now_button.Enable()
            
        else:
            
            self._check_now_button.Disable()
            
        
        if on_initial_sync:
            
            self._reset_cache_button.Disable()
            
        else:
            
            self._reset_cache_button.Enable()
            
        
    
    def _UpdateLastNextCheck( self ):
        
        if self._last_checked == 0:
            
            last_checked_text = 'initial check has not yet occured'
            
        else:
            
            last_checked_text = 'last checked ' + HydrusData.ConvertTimestampToPrettySync( self._last_checked )
            
        
        self._last_checked_st.SetLabelText( last_checked_text )
        
        periodic_next_check_time = self._last_checked + self._period.GetValue()
        error_next_check_time = self._last_error + HC.UPDATE_DURATION
        
        if self._check_now:
            
            next_check_text = 'next check as soon as manage subscriptions dialog is closed'
            
        elif error_next_check_time > periodic_next_check_time:
            
            next_check_text = 'due to an error, next check ' + HydrusData.ConvertTimestampToPrettyPending( error_next_check_time )
            
        else:
            
            next_check_text = 'next check ' + HydrusData.ConvertTimestampToPrettyPending( periodic_next_check_time )
            
        
        self._next_check_st.SetLabelText( next_check_text )
        
    
    def _UpdateSeedInfo( self ):
        
        seed_cache_text = HydrusData.ConvertIntToPrettyString( self._seed_cache.GetSeedCount() ) + ' urls in cache'
        
        num_failed = self._seed_cache.GetSeedCount( CC.STATUS_FAILED )
        
        if num_failed > 0:
            
            seed_cache_text += ', ' + HydrusData.ConvertIntToPrettyString( num_failed ) + ' failed'
            
        
        self._seed_info_st.SetLabelText( seed_cache_text )
        
    
    def _PresentForSiteType( self ):
        
        site_type = self._site_type.GetChoice()
        
        if site_type == HC.SITE_TYPE_BOORU:
            
            if self._booru_selector.GetCount() == 0:
                
                boorus = HydrusGlobals.client_controller.Read( 'remote_boorus' )
                
                for ( name, booru ) in boorus.items(): self._booru_selector.Append( name, booru )
                
                self._booru_selector.Select( 0 )
                
            
            self._booru_selector.Show()
            
        else:
            
            self._booru_selector.Hide()
            
        
        wx.CallAfter( self._ConfigureImportTagOptions )
        
        event = CC.SizeChangedEvent( -1 )
        
        wx.CallAfter( self.ProcessEvent, event )
        
    
    def CheckNow( self, event ):
        
        self._check_now = True
        
        self._UpdateCommandButtons()
        self._UpdateLastNextCheck()
        
    
    def EventBooruSelected( self, event ):
        
        self._ConfigureImportTagOptions()
        
    
    def EventPeriodChanged( self, event ):
        
        self._UpdateLastNextCheck()
        
    
    def EventSeedCache( self, event ):
        
        dupe_seed_cache = self._seed_cache.Duplicate()
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'file import status' ) as dlg:
            
            panel = EditSeedCachePanel( dlg, HydrusGlobals.client_controller, dupe_seed_cache )
            
            dlg.SetPanel( panel )
            
            if dlg.ShowModal() == wx.ID_OK:
                
                self._seed_cache = panel.GetValue()
                
                self._UpdateCommandButtons()
                self._UpdateSeedInfo()
                
            
        
        
    
    def EventSiteChanged( self, event ):
        
        self._PresentForSiteType()
        
    
    def GetValue( self ):
        
        name = self._name.GetValue()
        
        subscription = ClientImporting.Subscription( name )
        
        gallery_identifier = self._GetGalleryIdentifier()
        
        # in future, this can be harvested from some checkboxes or whatever for stream selection
        gallery_stream_identifiers = ClientDownloading.GetGalleryStreamIdentifiers( gallery_identifier )
        
        query = self._query.GetValue()
        
        period = self._period.GetValue()
        
        get_tags_if_redundant = self._get_tags_if_redundant.GetValue()
        initial_file_limit = self._initial_file_limit.GetValue()
        periodic_file_limit = self._periodic_file_limit.GetValue()
        
        paused = self._paused.GetValue()
        
        import_file_options = self._import_file_options.GetOptions()
        
        import_tag_options = self._import_tag_options.GetOptions()
        
        subscription.SetTuple( gallery_identifier, gallery_stream_identifiers, query, period, get_tags_if_redundant, initial_file_limit, periodic_file_limit, paused, import_file_options, import_tag_options, self._last_checked, self._last_error, self._check_now, self._seed_cache )
        
        return subscription
        
    
    def ResetCache( self, event ):
        
        message = '''Resetting this subscription's cache will delete ''' + HydrusData.ConvertIntToPrettyString( self._original_subscription.GetSeedCache().GetSeedCount() ) + ''' remembered urls, meaning when the subscription next runs, it will try to download those all over again. This may be expensive in time and data. Only do it if you are willing to wait. Do you want to do it?'''
        
        with ClientGUIDialogs.DialogYesNo( self, message ) as dlg:
            
            if dlg.ShowModal() == wx.ID_YES:
                
                self._last_checked = 0
                self._last_error = 0
                self._seed_cache = ClientImporting.SeedCache()
                
                self._UpdateCommandButtons()
                self._UpdateLastNextCheck()
                self._UpdateSeedInfo()
                
            
        
    
    def RetryFailed( self ):
        
        failed_seeds = self._seed_cache.GetSeeds( CC.STATUS_FAILED )
        
        for seed in failed_seeds:
            
            self._seed_cache.UpdateSeedStatus( seed, CC.STATUS_UNKNOWN )
            
        
        self._last_error = 0
        
        self._UpdateCommandButtons()
        self._UpdateLastNextCheck()
        self._UpdateSeedInfo()
        
    
