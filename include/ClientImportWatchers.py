import ClientConstants as CC
import ClientDownloading
import ClientImporting
import ClientImportOptions
import ClientImportFileSeeds
import ClientImportGallerySeeds
import ClientNetworkingJobs
import ClientParsing
import collections
import HydrusConstants as HC
import HydrusData
import HydrusExceptions
import HydrusGlobals as HG
import HydrusSerialisable
import threading
import time
import wx

class MultipleWatcherImport( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_MULTIPLE_WATCHER_IMPORT
    SERIALISABLE_NAME = 'Multiple Watcher'
    SERIALISABLE_VERSION = 2
    
    ADDED_TIMESTAMP_DURATION = 5
    
    def __init__( self, url = None ):
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        
        self._lock = threading.Lock()
        
        self._page_key = 'initialising page key'
        
        self._watchers = HydrusSerialisable.SerialisableList()
        
        self._highlighted_watcher_url = None
        
        self._checker_options = HG.client_controller.new_options.GetDefaultWatcherCheckerOptions()
        self._file_import_options = HG.client_controller.new_options.GetDefaultFileImportOptions( 'loud' )
        self._tag_import_options = ClientImportOptions.TagImportOptions( is_default = True )
        
        self._watcher_keys_to_watchers = {}
        
        self._watcher_keys_to_added_timestamps = {}
        self._watcher_keys_to_already_in_timestamps = {}
        
        self._watchers_repeating_job = None
        
        self._status_dirty = True
        self._status_cache = None
        self._status_cache_generation_time = 0
        
        #
        
        if url is not None:
            
            watcher = WatcherImport()
            
            watcher.SetURL( url )
            
            self._AddWatcher( watcher )
            
        
        self._last_pubbed_value_range = ( 0, 0 )
        self._next_pub_value_check_time = 0
        
    
    def _AddWatcher( self, watcher ):
        
        publish_to_page = False
        
        watcher.Repage( self._page_key, publish_to_page )
        
        self._watchers.append( watcher )
        
        watcher_key = watcher.GetWatcherKey()
        
        self._watcher_keys_to_watchers[ watcher_key ] = watcher
        self._watcher_keys_to_added_timestamps[ watcher_key ] = HydrusData.GetNow()
        
    
    def _CleanAddedTimestamps( self ):
        
        keys = list( self._watcher_keys_to_added_timestamps.keys() )
        
        for key in keys:
            
            if HydrusData.TimeHasPassed( self._watcher_keys_to_added_timestamps[ key ] + self.ADDED_TIMESTAMP_DURATION ):
                
                del self._watcher_keys_to_added_timestamps[ key ]
                
            
        
        keys = list( self._watcher_keys_to_already_in_timestamps.keys() )
        
        for key in keys:
            
            if HydrusData.TimeHasPassed( self._watcher_keys_to_already_in_timestamps[ key ] + self.ADDED_TIMESTAMP_DURATION ):
                
                del self._watcher_keys_to_already_in_timestamps[ key ]
                
            
        
    
    def _GetSerialisableInfo( self ):
        
        serialisable_watchers = self._watchers.GetSerialisableTuple()
        
        serialisable_checker_options = self._checker_options.GetSerialisableTuple()
        serialisable_file_import_options = self._file_import_options.GetSerialisableTuple()
        serialisable_tag_import_options = self._tag_import_options.GetSerialisableTuple()
        
        return ( serialisable_watchers, self._highlighted_watcher_url, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options )
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        ( serialisable_watchers, self._highlighted_watcher_url, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options ) = serialisable_info
        
        self._watchers = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_watchers )
        
        self._watcher_keys_to_watchers = { watcher.GetWatcherKey() : watcher for watcher in self._watchers }
        
        self._checker_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_checker_options )
        self._file_import_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_file_import_options )
        self._tag_import_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_tag_import_options )
        
    
    def _RegenerateStatus( self ):
        
        file_seed_caches = [ watcher.GetFileSeedCache() for watcher in self._watchers ]
        
        self._status_cache = ClientImportFileSeeds.GenerateFileSeedCachesStatus( file_seed_caches )
        
        self._status_dirty = False
        self._status_cache_generation_time = HydrusData.GetNow()
        
    
    def _RemoveWatcher( self, watcher_key ):
        
        if watcher_key not in self._watcher_keys_to_watchers:
            
            return
            
        
        watcher = self._watcher_keys_to_watchers[ watcher_key ]
        
        publish_to_page = False
        
        watcher.Repage( 'dead page key', publish_to_page )
        
        self._watchers.remove( watcher )
        
        del self._watcher_keys_to_watchers[ watcher_key ]
        
    
    def _SetDirty( self ):
        
        self._status_dirty = True
        
    
    def _UpdateSerialisableInfo( self, version, old_serialisable_info ):
        
        if version == 1:
            
            serialisable_watchers = old_serialisable_info
            
            try:
                
                checker_options = HG.client_controller.new_options.GetDefaultWatcherCheckerOptions()
                file_import_options = HG.client_controller.new_options.GetDefaultFileImportOptions( 'loud' )
                tag_import_options = ClientImportOptions.TagImportOptions( is_default = True )
                
            except:
                
                checker_options = ClientImportOptions.CheckerOptions()
                file_import_options = ClientImportOptions.FileImportOptions()
                tag_import_options = ClientImportOptions.TagImportOptions()
                
            
            serialisable_checker_options = checker_options.GetSerialisableTuple()
            serialisable_file_import_options = file_import_options.GetSerialisableTuple()
            serialisable_tag_import_options = tag_import_options.GetSerialisableTuple()
            
            highlighted_watcher_key = None
            
            serialisable_highlighted_watcher_key = highlighted_watcher_key
            
            new_serialisable_info = ( serialisable_watchers, serialisable_highlighted_watcher_key, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options )
            
            return ( 2, new_serialisable_info )
            
        
    
    def AddURL( self, url ):
        
        if url == '':
            
            return
            
        
        with self._lock:
            
            for watcher in self._watchers:
                
                if url == watcher.GetURL():
                    
                    watcher_key = watcher.GetWatcherKey()
                    
                    self._watcher_keys_to_already_in_timestamps[ watcher_key ] = HydrusData.GetNow()
                    
                    return
                    
                
            
            watcher = WatcherImport()
            
            watcher.SetURL( url )
            
            watcher.SetCheckerOptions( self._checker_options )
            watcher.SetFileImportOptions( self._file_import_options )
            watcher.SetTagImportOptions( self._tag_import_options )
            
            publish_to_page = False
            
            watcher.Start( self._page_key, publish_to_page )
            
            self._AddWatcher( watcher )
            
        
    
    def AddWatcher( self, watcher ):
        
        with self._lock:
            
            self._AddWatcher( watcher )
            
            self._SetDirty()
            
        
    
    def GetHighlightedWatcher( self ):
        
        with self._lock:
            
            if self._highlighted_watcher_url is not None:
                
                for watcher in self._watchers:
                    
                    if watcher.GetURL() == self._highlighted_watcher_url:
                        
                        return watcher
                        
                    
                
            
            self._highlighted_watcher_url = None
            
            return None
            
        
    
    def GetNumDead( self ):
        
        with self._lock:
            
            return len( [ watcher for watcher in self._watchers if watcher.IsDead() ] )
            
        
    
    def GetOptions( self ):
        
        with self._lock:
            
            return ( self._checker_options, self._file_import_options, self._tag_import_options )
            
        
    
    def GetTotalStatus( self ):
        
        with self._lock:
            
            if self._status_dirty:
                
                self._RegenerateStatus()
                
            
            return self._status_cache
            
        
    
    def GetValueRange( self ):
        
        with self._lock:
            
            total_value = 0
            total_range = 0
            
            for watcher in self._watchers:
                
                ( value, range ) = watcher.GetValueRange()
                
                if value != range:
                    
                    total_value += value
                    total_range += range
                    
                
            
            return ( total_value, total_range )
            
        
    
    def GetWatchers( self ):
        
        with self._lock:
            
            return list( self._watchers )
            
        
    
    def GetWatcherKeys( self ):
        
        with self._lock:
            
            return set( self._watcher_keys_to_watchers.keys() )
            
        
    
    def GetWatcherSimpleStatus( self, watcher ):
        
        with self._lock:
            
            watcher_key = watcher.GetWatcherKey()
            
            if watcher_key in self._watcher_keys_to_added_timestamps:
                
                added_timestamp = self._watcher_keys_to_added_timestamps[ watcher_key ]
                
                if HydrusData.TimeHasPassed( added_timestamp + self.ADDED_TIMESTAMP_DURATION ):
                    
                    self._CleanAddedTimestamps()
                    
                else:
                    
                    return 'just added'
                    
                
            
            if watcher_key in self._watcher_keys_to_already_in_timestamps:
                
                already_in_timestamp = self._watcher_keys_to_already_in_timestamps[ watcher_key ]
                
                if HydrusData.TimeHasPassed( already_in_timestamp + self.ADDED_TIMESTAMP_DURATION ):
                    
                    self._CleanAddedTimestamps()
                    
                else:
                    
                    return 'already watching'
                    
                
            
        
        return watcher.GetSimpleStatus()
        
    
    def RemoveWatcher( self, watcher_key ):
        
        with self._lock:
            
            self._RemoveWatcher( watcher_key )
            
            self._SetDirty()
            
        
    
    def SetHighlightedWatcher( self, highlighted_watcher ):
        
        with self._lock:
            
            if highlighted_watcher is None:
                
                self._highlighted_watcher_url = None
                
            else:
                
                self._highlighted_watcher_url = highlighted_watcher.GetURL()
                
            
        
    
    def SetOptions( self, checker_options, file_import_options, tag_import_options ):
        
        with self._lock:
            
            self._checker_options = checker_options
            self._file_import_options = file_import_options
            self._tag_import_options = tag_import_options
            
        
    
    def Start( self, page_key ):
        
        with self._lock:
            
            self._page_key = page_key
            
        
        # set a 2s period so the page value/range is breddy snappy
        self._watchers_repeating_job = HG.client_controller.CallRepeating( ClientImporting.GetRepeatingJobInitialDelay(), 2.0, self.REPEATINGWorkOnWatchers )
        
        publish_to_page = False
        
        for watcher in self._watchers:
            
            watcher.Start( page_key, publish_to_page )
            
        
    
    def REPEATINGWorkOnWatchers( self ):
        
        with self._lock:
            
            if ClientImporting.PageImporterShouldStopWorking( self._page_key ):
                
                self._watchers_repeating_job.Cancel()
                
                return
                
            
            if not self._status_dirty: # if we think we are clean
                
                for watcher in self._watchers:
                    
                    file_seed_cache = watcher.GetFileSeedCache()
                    
                    if file_seed_cache.GetStatusGenerationTime() > self._status_cache_generation_time: # has there has been an update?
                        
                        self._SetDirty()
                        
                        break
                        
                    
                
            
        
        if HydrusData.TimeHasPassed( self._next_pub_value_check_time ):
            
            self._next_pub_value_check_time = HydrusData.GetNow() + 5
            
            current_value_range = self.GetValueRange()
            
            if current_value_range != self._last_pubbed_value_range:
                
                self._last_pubbed_value_range = current_value_range
                
                HG.client_controller.pub( 'refresh_page_name', self._page_key )
                
            
        
        # something like:
            # if any are dead, do some stuff with them based on some options here
            # might want to have this work on a 30s period or something
        
    
HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_MULTIPLE_WATCHER_IMPORT ] = MultipleWatcherImport

class WatcherImport( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_WATCHER_IMPORT
    SERIALISABLE_NAME = 'Watcher'
    SERIALISABLE_VERSION = 6
    
    MIN_CHECK_PERIOD = 30
    
    def __init__( self ):
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        
        self._page_key = 'initialising page key'
        self._publish_to_page = False
        
        self._url = ''
        
        self._gallery_seed_log = ClientImportGallerySeeds.GallerySeedLog()
        self._file_seed_cache = ClientImportFileSeeds.FileSeedCache()
        
        self._urls_to_filenames = {}
        self._urls_to_md5_base64 = {}
        self._checker_options = HG.client_controller.new_options.GetDefaultWatcherCheckerOptions()
        self._file_import_options = HG.client_controller.new_options.GetDefaultFileImportOptions( 'loud' )
        self._tag_import_options = ClientImportOptions.TagImportOptions( is_default = True )
        self._last_check_time = 0
        self._checking_status = ClientImporting.CHECKER_STATUS_OK
        self._subject = 'unknown subject'
        
        self._next_check_time = None
        
        self._download_control_file_set = None
        self._download_control_file_clear = None
        self._download_control_checker_set = None
        self._download_control_checker_clear = None
        
        self._check_now = False
        self._files_paused = False
        self._checking_paused = False
        
        self._no_work_until = 0
        self._no_work_until_reason = ''
        
        self._creation_time = HydrusData.GetNow()
        
        self._file_velocity_status = ''
        self._current_action = ''
        self._watcher_status = ''
        
        self._watcher_key = HydrusData.GenerateKey()
        
        self._lock = threading.Lock()
        
        self._last_pubbed_page_name = ''
        
        self._files_repeating_job = None
        self._checker_repeating_job = None
        
        HG.client_controller.sub( self, 'NotifyFileSeedsUpdated', 'file_seed_cache_file_seeds_updated' )
        
    
    def _CheckWatchableURL( self ):
        
        def status_hook( text ):
            
            with self._lock:
                
                self._watcher_status = text
                
            
        
        def title_hook( text ):
            
            with self._lock:
                
                self._subject = text
                
            
        
        gallery_seed = ClientImportGallerySeeds.GallerySeed( self._url, can_generate_more_pages = False )
        
        self._gallery_seed_log.AddGallerySeeds( ( gallery_seed, ) )
        
        try:
            
            ( num_urls_added, added_all_possible_urls, result_404 ) = gallery_seed.WorkOnURL( self._gallery_seed_log, self._file_seed_cache, status_hook, title_hook, ClientImporting.GenerateWatcherNetworkJobFactory( self._watcher_key ), self._CheckerNetworkJobPresentationContextFactory, self._file_import_options )
            
            if num_urls_added > 0:
                
                ClientImporting.WakeRepeatingJob( self._files_repeating_job )
                
            
            if result_404:
                
                with self._lock:
                    
                    self._checking_status = ClientImporting.CHECKER_STATUS_404
                    
                
            
        except HydrusExceptions.NetworkException as e:
            
            self._DelayWork( 4 * 3600, HydrusData.ToUnicode( e ) )
            
            HydrusData.PrintException( e )
            
        
        watcher_status = gallery_seed.note
        error_occurred = gallery_seed.status == CC.STATUS_ERROR
        watcher_status_should_stick = gallery_seed.status != CC.STATUS_SUCCESSFUL_AND_NEW
        
        self._FinishCheck( watcher_status, error_occurred, watcher_status_should_stick )
        
    
    def _DelayWork( self, time_delta, reason ):
        
        self._no_work_until = HydrusData.GetNow() + time_delta
        self._no_work_until_reason = reason
        
    
    def _FileNetworkJobPresentationContextFactory( self, network_job ):
        
        def enter_call():
            
            with self._lock:
                
                if self._download_control_file_set is not None:
                    
                    wx.CallAfter( self._download_control_file_set, network_job )
                    
                
            
        
        def exit_call():
            
            with self._lock:
                
                if self._download_control_file_clear is not None:
                    
                    wx.CallAfter( self._download_control_file_clear )
                    
                
            
        
        return ClientImporting.NetworkJobPresentationContext( enter_call, exit_call )
        
    
    def _FinishCheck( self, watcher_status, error_occurred, watcher_status_should_stick ):
        
        if error_occurred:
            
            # the [DEAD] stuff can override watcher status, so let's give a brief time for this to display the error
            
            with self._lock:
                
                self._checking_paused = True
                
                self._watcher_status = watcher_status
                
            
            time.sleep( 5 )
            
        
        with self._lock:
            
            if self._check_now:
                
                self._check_now = False
                
            
            self._watcher_status = watcher_status
            
            self._last_check_time = HydrusData.GetNow()
            
            self._UpdateFileVelocityStatus()
            
            self._UpdateNextCheckTime()
            
            self._PublishPageName()
            
        
        if not watcher_status_should_stick:
            
            time.sleep( 5 )
            
            with self._lock:
                
                self._watcher_status = ''
                
            
        
    
    def _GetSerialisableInfo( self ):
        
        serialisable_gallery_seed_log = self._gallery_seed_log.GetSerialisableTuple()
        serialisable_file_seed_cache = self._file_seed_cache.GetSerialisableTuple()
        
        serialisable_checker_options = self._checker_options.GetSerialisableTuple()
        serialisable_file_import_options = self._file_import_options.GetSerialisableTuple()
        serialisable_tag_import_options = self._tag_import_options.GetSerialisableTuple()
        
        return ( self._url, serialisable_gallery_seed_log, serialisable_file_seed_cache, self._urls_to_filenames, self._urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, self._last_check_time, self._files_paused, self._checking_paused, self._checking_status, self._subject, self._no_work_until, self._no_work_until_reason, self._creation_time )
        
    
    def _HasURL( self ):
        
        return self._url != ''
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        ( self._url, serialisable_gallery_seed_log, serialisable_file_seed_cache, self._urls_to_filenames, self._urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, self._last_check_time, self._files_paused, self._checking_paused, self._checking_status, self._subject, self._no_work_until, self._no_work_until_reason, self._creation_time ) = serialisable_info
        
        self._gallery_seed_log = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_gallery_seed_log )
        self._file_seed_cache = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_file_seed_cache )
        
        self._checker_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_checker_options )
        self._file_import_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_file_import_options )
        self._tag_import_options = HydrusSerialisable.CreateFromSerialisableTuple( serialisable_tag_import_options )
        
    
    def _PublishPageName( self ):
        
        new_options = HG.client_controller.new_options
        
        cannot_rename = not new_options.GetBoolean( 'permit_watchers_to_name_their_pages' )
        
        if cannot_rename:
            
            page_name = 'watcher'
            
        elif self._subject in ( '', 'unknown subject' ):
            
            page_name = 'watcher'
            
        else:
            
            page_name = self._subject
            
        
        if self._checking_status == ClientImporting.CHECKER_STATUS_404:
            
            thread_watcher_not_found_page_string = new_options.GetNoneableString( 'thread_watcher_not_found_page_string' )
            
            if thread_watcher_not_found_page_string is not None:
                
                page_name = thread_watcher_not_found_page_string + ' ' + page_name
                
            
        elif self._checking_status == ClientImporting.CHECKER_STATUS_DEAD:
            
            thread_watcher_dead_page_string = new_options.GetNoneableString( 'thread_watcher_dead_page_string' )
            
            if thread_watcher_dead_page_string is not None:
                
                page_name = thread_watcher_dead_page_string + ' ' + page_name
                
            
        elif self._checking_paused:
            
            thread_watcher_paused_page_string = new_options.GetNoneableString( 'thread_watcher_paused_page_string' )
            
            if thread_watcher_paused_page_string is not None:
                
                page_name = thread_watcher_paused_page_string + ' ' + page_name
                
            
        
        if page_name != self._last_pubbed_page_name:
            
            self._last_pubbed_page_name = page_name
            
            if self._publish_to_page:
                
                HG.client_controller.pub( 'rename_page', self._page_key, page_name )
                
            
        
        
    
    def _CheckerNetworkJobPresentationContextFactory( self, network_job ):
        
        def enter_call():
            
            with self._lock:
                
                if self._download_control_checker_set is not None:
                    
                    wx.CallAfter( self._download_control_checker_set, network_job )
                    
                
            
        
        def exit_call():
            
            with self._lock:
                
                if self._download_control_checker_clear is not None:
                    
                    wx.CallAfter( self._download_control_checker_clear )
                    
                
            
        
        return ClientImporting.NetworkJobPresentationContext( enter_call, exit_call )
        
    
    def _UpdateFileVelocityStatus( self ):
        
        self._file_velocity_status = self._checker_options.GetPrettyCurrentVelocity( self._file_seed_cache, self._last_check_time )
        
    
    def _UpdateNextCheckTime( self ):
        
        if self._check_now:
            
            self._next_check_time = self._last_check_time + self.MIN_CHECK_PERIOD
            
        else:
            
            if not HydrusData.TimeHasPassed( self._no_work_until ):
                
                self._next_check_time = self._no_work_until + 1
                
            else:
                
                if self._checking_status != ClientImporting.CHECKER_STATUS_404:
                    
                    if self._checker_options.IsDead( self._file_seed_cache, self._last_check_time ):
                        
                        self._checking_status = ClientImporting.CHECKER_STATUS_DEAD
                        
                        self._checking_paused = True
                        
                    
                
                last_next_check_time = self._next_check_time
                
                self._next_check_time = self._checker_options.GetNextCheckTime( self._file_seed_cache, self._last_check_time, last_next_check_time )
                
            
        
    
    def _UpdateSerialisableInfo( self, version, old_serialisable_info ):
        
        if version == 1:
            
            ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_file_import_options, serialisable_tag_import_options, times_to_check, check_period, last_check_time, paused ) = old_serialisable_info
            
            checker_options = ClientImportOptions.CheckerOptions( intended_files_per_check = 8, never_faster_than = 300, never_slower_than = 86400, death_file_velocity = ( 1, 86400 ) )
            
            serialisable_checker_options = checker_options.GetSerialisableTuple()
            
            files_paused = paused
            checking_paused = paused
            
            new_serialisable_info = ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused )
            
            return ( 2, new_serialisable_info )
            
        
        if version == 2:
            
            ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused ) = old_serialisable_info
            
            checking_status = ClientImporting.CHECKER_STATUS_OK
            subject = 'unknown subject'
            
            new_serialisable_info = ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject )
            
            return ( 3, new_serialisable_info )
            
        
        if version == 3:
            
            ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject ) = old_serialisable_info
            
            no_work_until = 0
            no_work_until_reason = ''
            
            new_serialisable_info = ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject, no_work_until, no_work_until_reason )
            
            return ( 4, new_serialisable_info )
            
        
        if version == 4:
            
            ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject, no_work_until, no_work_until_reason ) = old_serialisable_info
            
            creation_time = HydrusData.GetNow()
            
            new_serialisable_info = ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject, no_work_until, no_work_until_reason, creation_time )
            
            return ( 5, new_serialisable_info )
            
        
        if version == 5:
            
            ( url, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject, no_work_until, no_work_until_reason, creation_time ) = old_serialisable_info
            
            gallery_seed_log = ClientImportGallerySeeds.GallerySeedLog()
            
            serialisable_gallery_seed_log = gallery_seed_log.GetSerialisableTuple()
            
            new_serialisable_info = ( url, serialisable_gallery_seed_log, serialisable_file_seed_cache, urls_to_filenames, urls_to_md5_base64, serialisable_checker_options, serialisable_file_import_options, serialisable_tag_import_options, last_check_time, files_paused, checking_paused, checking_status, subject, no_work_until, no_work_until_reason, creation_time )
            
            return ( 6, new_serialisable_info )
            
        
    
    def _WorkOnFiles( self ):
        
        file_seed = self._file_seed_cache.GetNextFileSeed( CC.STATUS_UNKNOWN )
        
        if file_seed is None:
            
            return
            
        
        did_substantial_work = False
        
        def status_hook( text ):
            
            with self._lock:
                
                self._current_action = text
                
            
        
        did_substantial_work = file_seed.WorkOnURL( self._file_seed_cache, status_hook, ClientImporting.GenerateWatcherNetworkJobFactory( self._watcher_key ), self._FileNetworkJobPresentationContextFactory, self._file_import_options, self._tag_import_options )
        
        with self._lock:
            
            should_present = self._publish_to_page and file_seed.ShouldPresent( self._file_import_options )
            
            page_key = self._page_key
            
        
        if should_present:
            
            file_seed.PresentToPage( page_key )
            
            did_substantial_work = True
            
        
        with self._lock:
            
            self._current_action = ''
            
        
        if did_substantial_work:
            
            time.sleep( ClientImporting.DID_SUBSTANTIAL_FILE_WORK_MINIMUM_SLEEP_TIME )
            
        
    
    def CheckNow( self ):
        
        with self._lock:
            
            self._check_now = True
            
            self._checking_paused = False
            
            self._no_work_until = 0
            self._no_work_until_reason = ''
            
            self._checking_status = ClientImporting.CHECKER_STATUS_OK
            
            self._UpdateNextCheckTime()
            
            ClientImporting.WakeRepeatingJob( self._checker_repeating_job )
            
        
    
    def CurrentlyAlive( self ):
        
        with self._lock:
            
            return self._checking_status == ClientImporting.CHECKER_STATUS_OK
            
        
    
    def CurrentlyWorking( self ):
        
        with self._lock:
            
            finished = not self._file_seed_cache.WorkToDo()
            
            return not finished and not self._files_paused
            
        
    
    def GetCheckerOptions( self ):
        
        with self._lock:
            
            return self._checker_options
            
        
    
    def GetCreationTime( self ):
        
        with self._lock:
            
            return self._creation_time
            
        
    
    def GetOptions( self ):
        
        with self._lock:
            
            return ( self._url, self._file_import_options, self._tag_import_options )
            
        
    
    def GetPresentedHashes( self ):
        
        return self._file_seed_cache.GetPresentedHashes( self._file_import_options )
        
    
    def GetFileSeedCache( self ):
        
        return self._file_seed_cache
        
    
    def GetGallerySeedLog( self ):
        
        return self._gallery_seed_log
        
    
    def GetSimpleStatus( self ):
        
        with self._lock:
            
            if self._checking_status == ClientImporting.CHECKER_STATUS_404:
                
                return '404'
                
            elif self._checking_status == ClientImporting.CHECKER_STATUS_DEAD:
                
                return 'DEAD'
                
            elif self._checking_paused or self._files_paused:
                
                return 'paused'
                
            else:
                
                return ''
                
            
        
    
    def GetStatus( self ):
        
        with self._lock:
            
            if self._checking_status == ClientImporting.CHECKER_STATUS_404:
                
                watcher_status = 'URL 404'
                
            elif self._checking_status == ClientImporting.CHECKER_STATUS_DEAD:
                
                watcher_status = 'URL DEAD'
                
            elif not HydrusData.TimeHasPassed( self._no_work_until ):
                
                watcher_status = self._no_work_until_reason + ' - ' + 'next check ' + HydrusData.TimestampToPrettyTimeDelta( self._next_check_time )
                
            else:
                
                watcher_status = self._watcher_status
                
            
            return ( self._current_action, self._files_paused, self._file_velocity_status, self._next_check_time, watcher_status, self._subject, self._checking_status, self._check_now, self._checking_paused )
            
        
    
    def GetSubject( self ):
        
        with self._lock:
            
            if self._subject in ( None, '' ):
                
                return 'unknown subject'
                
            else:
                
                return self._subject
                
            
        
    
    def GetWatcherKey( self ):
        
        with self._lock:
            
            return self._watcher_key
            
        
    
    def GetURL( self ):
        
        with self._lock:
            
            return self._url
            
        
    
    def GetValueRange( self ):
        
        with self._lock:
            
            return self._file_seed_cache.GetValueRange()
            
        
    
    def HasURL( self ):
        
        with self._lock:
            
            return self._HasURL()
            
        
    
    def _IsDead( self ):
        
        return self._checking_status in ( ClientImporting.CHECKER_STATUS_404, ClientImporting.CHECKER_STATUS_DEAD )
        
    
    def IsDead( self ):
        
        with self._lock:
            
            return self._IsDead()
            
        
    
    def NotifyFileSeedsUpdated( self, file_seed_cache_key, file_seeds ):
        
        if file_seed_cache_key == self._file_seed_cache.GetFileSeedCacheKey():
            
            ClientImporting.WakeRepeatingJob( self._files_repeating_job )
            
        
    
    def PausePlayChecker( self ):
        
        with self._lock:
            
            if self._checking_paused and self._IsDead():
                
                return # watcher is dead, so don't unpause until a checknow event
                
            else:
                
                self._checking_paused = not self._checking_paused
                
                ClientImporting.WakeRepeatingJob( self._checker_repeating_job )
                
            
        
    
    def PausePlayFiles( self ):
        
        with self._lock:
            
            self._files_paused = not self._files_paused
            
            ClientImporting.WakeRepeatingJob( self._files_repeating_job )
            
        
    
    def PausePlay( self ):
        
        with self._lock:
            
            if self._checking_paused:
                
                if self._IsDead(): # can't unpause checker until a checknow event
                    
                    self._files_paused = not self._files_paused
                    
                else:
                    
                    self._checking_paused = False
                    self._files_paused = False
                    
                
                ClientImporting.WakeRepeatingJob( self._checker_repeating_job )
                ClientImporting.WakeRepeatingJob( self._files_repeating_job )
                
            else:
                
                self._checking_paused = True
                self._files_paused = True
                
            
        
    
    def Repage( self, page_key, publish_to_page ):
        
        with self._lock:
            
            self._page_key = page_key
            self._publish_to_page = publish_to_page
            
        
    
    def SetCheckerOptions( self, checker_options ):
        
        with self._lock:
            
            self._checker_options = checker_options
            
            self._checking_paused = False
            
            self._UpdateNextCheckTime()
            
            self._UpdateFileVelocityStatus()
            
            ClientImporting.WakeRepeatingJob( self._checker_repeating_job )
            
        
    
    def SetDownloadControlChecker( self, download_control ):
        
        with self._lock:
            
            self._download_control_checker_set = download_control.SetNetworkJob
            self._download_control_checker_clear = download_control.ClearNetworkJob
            
        
    
    def SetDownloadControlFile( self, download_control ):
        
        with self._lock:
            
            self._download_control_file_set = download_control.SetNetworkJob
            self._download_control_file_clear = download_control.ClearNetworkJob
            
        
    
    def SetFileImportOptions( self, file_import_options ):
        
        with self._lock:
            
            self._file_import_options = file_import_options
            
        
    
    def SetTagImportOptions( self, tag_import_options ):
        
        with self._lock:
            
            self._tag_import_options = tag_import_options
            
        
    
    def SetURL( self, url ):
        
        if url is None:
            
            url = ''
            
        
        if url != '':
            
            url = HG.client_controller.network_engine.domain_manager.NormaliseURL( url )
            
        
        with self._lock:
            
            self._url = url
            
            ClientImporting.WakeRepeatingJob( self._checker_repeating_job )
            
        
    
    def Start( self, page_key, publish_to_page ):
        
        self._page_key = page_key
        self._publish_to_page = publish_to_page
        
        self._UpdateNextCheckTime()
        
        self._PublishPageName()
        
        self._UpdateFileVelocityStatus()
        
        self._files_repeating_job = HG.client_controller.CallRepeating( ClientImporting.GetRepeatingJobInitialDelay(), ClientImporting.REPEATING_JOB_TYPICAL_PERIOD, self.REPEATINGWorkOnFiles )
        self._checker_repeating_job = HG.client_controller.CallRepeating( ClientImporting.GetRepeatingJobInitialDelay(), ClientImporting.REPEATING_JOB_TYPICAL_PERIOD, self.REPEATINGWorkOnChecker )
        
    
    def REPEATINGWorkOnFiles( self ):
        
        with self._lock:
            
            if ClientImporting.PageImporterShouldStopWorking( self._page_key ):
                
                self._files_repeating_job.Cancel()
                
                return
                
            
            work_to_do = self._file_seed_cache.WorkToDo() and not ( self._files_paused or HG.client_controller.PageClosedButNotDestroyed( self._page_key ) )
            
        
        while work_to_do:
            
            try:
                
                self._WorkOnFiles()
                
                HG.client_controller.WaitUntilViewFree()
                
            except Exception as e:
                
                HydrusData.ShowException( e )
                
            
            with self._lock:
                
                if ClientImporting.PageImporterShouldStopWorking( self._page_key ):
                    
                    self._files_repeating_job.Cancel()
                    
                    return
                    
                
                work_to_do = self._file_seed_cache.WorkToDo() and not ( self._files_paused or HG.client_controller.PageClosedButNotDestroyed( self._page_key ) )
                
            
        
    
    def REPEATINGWorkOnChecker( self ):
        
        with self._lock:
            
            if ClientImporting.PageImporterShouldStopWorking( self._page_key ):
                
                self._checker_repeating_job.Cancel()
                
                return
                
            
            able_to_check = self._HasURL() and not self._checking_paused
            check_due = HydrusData.TimeHasPassed( self._next_check_time )
            no_delays = HydrusData.TimeHasPassed( self._no_work_until )
            page_shown = not HG.client_controller.PageClosedButNotDestroyed( self._page_key )
            
            time_to_check = able_to_check and check_due and no_delays and page_shown
            
        
        if time_to_check:
            
            try:
                
                self._CheckWatchableURL()
                
            except Exception as e:
                
                HydrusData.ShowException( e )
                
            
        
    
HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_WATCHER_IMPORT ] = WatcherImport
