import ClientConstants as CC
import ClientGUIDialogs
import collections
import HydrusConstants as HC
import HydrusData
import HydrusGlobals as HG
import HydrusSerialisable
import HydrusTagArchive
import HydrusTags
import os
import threading
import wx

def ConvertTagSliceToString( tag_slice ):
    
    if tag_slice == '':
        
        return 'unnamespaced tags'
        
    elif tag_slice == ':':
        
        return 'namespaced tags'
        
    elif tag_slice.count( ':' ) == 1 and tag_slice.endswith( ':' ):
        
        namespace = tag_slice[ : -1 ]
        
        return '\'' + namespace + '\' tags'
        
    else:
        
        return tag_slice
        
    
def ExportToHTA( parent, service_key, hashes ):
    
    with wx.FileDialog( parent, style = wx.FD_SAVE, defaultFile = 'archive.db' ) as dlg:
        
        if dlg.ShowModal() == wx.ID_OK:
            
            path = HydrusData.ToUnicode( dlg.GetPath() )
            
        else:
            
            return
            
        
    
    message = 'Would you like to use hydrus\'s normal hash type, or an alternative?'
    message += os.linesep * 2
    message += 'Hydrus uses SHA256 to identify files, but other services use different standards. MD5, SHA1 and SHA512 are available, but only for local files, which may limit your export.'
    message += os.linesep * 2
    message += 'If you do not know what this stuff means, click \'normal\'.'
    
    with ClientGUIDialogs.DialogYesNo( parent, message, title = 'Choose which hash type.', yes_label = 'normal', no_label = 'alternative' ) as dlg:
        
        result = dlg.ShowModal()
        
        if result in ( wx.ID_YES, wx.ID_NO ):
            
            if result == wx.ID_YES:
                
                hash_type = HydrusTagArchive.HASH_TYPE_SHA256
                
            else:
                
                list_of_tuples = []
                
                list_of_tuples.append( ( 'md5', HydrusTagArchive.HASH_TYPE_MD5 ) )
                list_of_tuples.append( ( 'sha1', HydrusTagArchive.HASH_TYPE_SHA1 ) )
                list_of_tuples.append( ( 'sha512', HydrusTagArchive.HASH_TYPE_SHA512 ) )
                
                with ClientGUIDialogs.DialogSelectFromList( parent, 'Select the hash type', list_of_tuples ) as hash_dlg:
                    
                    if hash_dlg.ShowModal() == wx.ID_OK:
                        
                        hash_type = hash_dlg.GetChoice()
                        
                    else:
                        
                        return
                        
                    
                
            
        
    
    if hash_type is not None:
        
        HG.client_controller.Write( 'export_mappings', path, service_key, hash_type, hashes )
        
    
def ImportFromHTA( parent, hta_path, tag_service_key, hashes ):
    
    hta = HydrusTagArchive.HydrusTagArchive( hta_path )
    
    potential_namespaces = list( hta.GetNamespaces() )
    
    potential_namespaces.sort()
    
    hash_type = hta.GetHashType() # this tests if the hta can produce a hashtype
    
    del hta
    
    service = HG.client_controller.services_manager.GetService( tag_service_key )
    
    service_type = service.GetServiceType()
    
    can_delete = True
    
    if service_type == HC.TAG_REPOSITORY:
        
        if service.HasPermission( HC.CONTENT_TYPE_MAPPINGS, HC.PERMISSION_ACTION_OVERRULE ):
            
            can_delete = False
            
        
    
    if can_delete:
        
        text = 'Would you like to add or delete the archive\'s tags?'
        
        with ClientGUIDialogs.DialogYesNo( parent, text, title = 'Add or delete?', yes_label = 'add', no_label = 'delete' ) as dlg_add:
            
            result = dlg_add.ShowModal()
            
            if result == wx.ID_YES: adding = True
            elif result == wx.ID_NO: adding = False
            else: return
            
        
    else:
        
        text = 'You cannot quickly delete tags from this service, so I will assume you want to add tags.'
        
        wx.MessageBox( text )
        
        adding = True
        
    
    text = 'Choose which namespaces to '
    
    if adding: text += 'add.'
    else: text += 'delete.'
    
    list_of_tuples = [ ( HydrusData.ConvertUglyNamespaceToPrettyString( namespace ), namespace, False ) for namespace in potential_namespaces ]
    
    with ClientGUIDialogs.DialogCheckFromList( parent, text, list_of_tuples ) as dlg_namespaces:
        
        if dlg_namespaces.ShowModal() == wx.ID_OK:
            
            namespaces = dlg_namespaces.GetChecked()
            
            if hash_type == HydrusTagArchive.HASH_TYPE_SHA256:
                
                text = 'This tag archive can be fully merged into your database, but this may be more than you want.'
                text += os.linesep * 2
                text += 'Would you like to import the tags only for files you actually have, or do you want absolutely everything?'
                
                with ClientGUIDialogs.DialogYesNo( parent, text, title = 'How much do you want?', yes_label = 'just for my local files', no_label = 'everything' ) as dlg_add:
                    
                    result = dlg_add.ShowModal()
                    
                    if result == wx.ID_YES:
                        
                        file_service_key = CC.LOCAL_FILE_SERVICE_KEY
                        
                    elif result == wx.ID_NO:
                        
                        file_service_key = CC.COMBINED_FILE_SERVICE_KEY
                        
                    else:
                        
                        return
                        
                    
                
            else:
                
                file_service_key = CC.LOCAL_FILE_SERVICE_KEY
                
            
            text = 'Are you absolutely sure you want to '
            
            if adding: text += 'add'
            else: text += 'delete'
            
            text += ' the namespaces:'
            text += os.linesep * 2
            text += os.linesep.join( HydrusData.ConvertUglyNamespacesToPrettyStrings( namespaces ) )
            text += os.linesep * 2
            
            file_service = HG.client_controller.services_manager.GetService( file_service_key )
            
            text += 'For '
            
            if hashes is None:
                
                text += 'all'
                
            else:
                
                text += HydrusData.ToHumanInt( len( hashes ) )
                
            
            text += ' files in \'' + file_service.GetName() + '\''
            
            if adding: text += ' to '
            else: text += ' from '
            
            text += '\'' + service.GetName() + '\'?'
            
            with ClientGUIDialogs.DialogYesNo( parent, text ) as dlg_final:
                
                if dlg_final.ShowModal() == wx.ID_YES:
                    
                    HG.client_controller.pub( 'sync_to_tag_archive', hta_path, tag_service_key, file_service_key, adding, namespaces, hashes )
                    
                
            
        
    
def RenderNamespaceForUser( namespace ):
    
    if namespace == '' or namespace is None:
        
        return 'unnamespaced'
        
    else:
        
        return namespace
        
    
def RenderTag( tag, render_for_user ):
    
    ( namespace, subtag ) = HydrusTags.SplitTag( tag )
    
    if namespace == '':
        
        return subtag
        
    else:
        
        if render_for_user:
            
            new_options = HG.client_controller.new_options
            
            if new_options.GetBoolean( 'show_namespaces' ):
                
                connector = new_options.GetString( 'namespace_connector' )
                
            else:
                
                return subtag
                
            
        else:
            
            connector = ':'
            
        
        return namespace + connector + subtag
        
    
def SortTagsList( tags, sort_type ):
    
    if sort_type in ( CC.SORT_BY_LEXICOGRAPHIC_DESC, CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_DESC ):
        
        reverse = True
        
    else:
        
        reverse = False
        
    
    if sort_type in ( CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_ASC, CC.SORT_BY_LEXICOGRAPHIC_NAMESPACE_DESC ):
        
        def key( tag ):
            
            # '{' is above 'z' in ascii, so this works for most situations
            
            ( namespace, subtag ) = HydrusTags.SplitTag( tag )
            
            if namespace == '':
                
                return ( '{', subtag )
                
            else:
                
                return ( namespace, subtag )
                
            
        
    else:
        
        key = None
        
    
    tags.sort( key = key, reverse = reverse )
    
class TagFilter( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_TAG_FILTER
    SERIALISABLE_NAME = 'Tag Filter Rules'
    SERIALISABLE_VERSION = 1
    
    def __init__( self ):
        
        HydrusSerialisable.SerialisableBase.__init__( self )
        
        self._lock = threading.Lock()
        
        self._tag_slices_to_rules = {}
        
    
    def __eq__( self, other ):
        
        return self._tag_slices_to_rules == other._tag_slices_to_rules
        
    
    def _GetRulesForTag( self, tag ):
        
        rules = []
        tag_slices = []
        
        ( namespace, subtag ) = HydrusTags.SplitTag( tag )
        
        tag_slices.append( tag )
        
        if namespace != '':
            
            tag_slices.append( namespace + ':' )
            tag_slices.append( ':' )
            
        else:
            
            tag_slices.append( '' )
            
        
        for tag_slice in tag_slices:
            
            if tag_slice in self._tag_slices_to_rules:
                
                rule = self._tag_slices_to_rules[ tag_slice ]
                
                rules.append( rule )
                
            
        
        return rules
        
    
    def _GetSerialisableInfo( self ):
        
        return self._tag_slices_to_rules.items()
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        self._tag_slices_to_rules = dict( serialisable_info )
        
    
    def _TagOK( self, tag ):
        
        rules = self._GetRulesForTag( tag )
        
        if CC.FILTER_WHITELIST in rules: # There is an exception for this tag
            
            return True
            
        elif CC.FILTER_BLACKLIST in rules: # There is a rule against this tag
            
            return False
            
        else: # There are no rules for this tag
            
            return True
            
        
    
    def Filter( self, tags ):
        
        with self._lock:
            
            return { tag for tag in tags if self._TagOK( tag ) }
            
        
    
    def GetTagSlicesToRules( self ):
        
        with self._lock:
            
            return dict( self._tag_slices_to_rules )
            
        
    
    def SetRule( self, tag_slice, rule ):
        
        with self._lock:
            
            self._tag_slices_to_rules[ tag_slice ] = rule
            
        
    
    def ToBlacklistString( self ):
        
        blacklist = []
        whitelist = []
        
        for ( tag_slice, rule ) in self._tag_slices_to_rules.items():
            
            if rule == CC.FILTER_BLACKLIST:
                
                blacklist.append( tag_slice )
                
            elif rule == CC.FILTER_WHITELIST:
                
                whitelist.append( tag_slice )
                
            
        
        blacklist.sort()
        whitelist.sort()
        
        if len( blacklist ) == 0:
            
            return 'no blacklist set'
            
        else:
            
            if set( blacklist ) == { '', ':' }:
                
                text = 'blacklisting on any tags'
                
            else:
                
                text = 'blacklisting on ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in blacklist ) )
                
            
            if len( whitelist ) > 0:
                
                text += ' except ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in whitelist ) )
                
            
            return text
            
        
    
    def ToCensoredString( self ):
        
        blacklist = []
        whitelist = []
        
        for ( tag_slice, rule ) in self._tag_slices_to_rules.items():
            
            if rule == CC.FILTER_BLACKLIST:
                
                blacklist.append( tag_slice )
                
            elif rule == CC.FILTER_WHITELIST:
                
                whitelist.append( tag_slice )
                
            
        
        blacklist.sort()
        whitelist.sort()
        
        if len( blacklist ) == 0:
            
            return 'all tags allowed'
            
        else:
            
            if set( blacklist ) == { '', ':' }:
                
                text = 'no tags allowed'
                
            else:
                
                text = 'all but ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in blacklist ) ) + ' allowed'
                
            
            if len( whitelist ) > 0:
                
                text += ' except ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in whitelist ) )
                
            
            return text
            
        
    
    def ToPermittedString( self ):
        
        blacklist = []
        whitelist = []
        
        for ( tag_slice, rule ) in self._tag_slices_to_rules.items():
            
            if rule == CC.FILTER_BLACKLIST:
                
                blacklist.append( tag_slice )
                
            elif rule == CC.FILTER_WHITELIST:
                
                whitelist.append( tag_slice )
                
            
        
        blacklist.sort()
        whitelist.sort()
        
        if len( blacklist ) == 0:
            
            return 'all tags'
            
        else:
            
            if set( blacklist ) == { '', ':' }:
                
                if len( whitelist ) == 0:
                    
                    text = 'no tags'
                    
                else:
                    
                    text = 'only ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in whitelist ) )
                    
                
            else:
                
                text = 'all tags except ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in blacklist ) )
                
                if len( whitelist ) > 0:
                    
                    text += ' (except ' + ', '.join( ( ConvertTagSliceToString( tag_slice ) for tag_slice in whitelist ) ) + ')'
                    
                
            
        
        return text
        
    
HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_TAG_FILTER ] = TagFilter

class TagSummaryGenerator( HydrusSerialisable.SerialisableBase ):
    
    SERIALISABLE_TYPE = HydrusSerialisable.SERIALISABLE_TYPE_TAG_SUMMARY_GENERATOR
    SERIALISABLE_NAME = 'Tag Summary Generator'
    SERIALISABLE_VERSION = 2
    
    def __init__( self, background_colour = None, text_colour = None, namespace_info = None, separator = None, example_tags = None, show = True ):
        
        if background_colour is None:
            
            background_colour = wx.Colour( 223, 227, 230, 255 )
            
        
        if text_colour is None:
            
            text_colour = wx.Colour( 1, 17, 26, 255 )
            
        
        if namespace_info is None:
            
            namespace_info = []
            
            namespace_info.append( ( 'creator', '', ', ' ) )
            namespace_info.append( ( 'series', '', ', ' ) )
            namespace_info.append( ( 'title', '', ', ' ) )
            
        
        if separator is None:
            
            separator = ' - '
            
        
        if example_tags is None:
            
            example_tags = []
            
        
        self._background_colour = background_colour
        self._text_colour = text_colour
        self._namespace_info = namespace_info
        self._separator = separator
        self._example_tags = list( example_tags )
        self._show = show
        
        self._UpdateNamespaceLookup()
        
    
    def _GetSerialisableInfo( self ):
        
        return ( list( self._background_colour.Get() ), list( self._text_colour.Get() ), self._namespace_info, self._separator, self._example_tags, self._show )
        
    
    def _InitialiseFromSerialisableInfo( self, serialisable_info ):
        
        ( background_rgba, text_rgba, self._namespace_info, self._separator, self._example_tags, self._show ) = serialisable_info
        
        ( r, g, b, a ) = background_rgba
        
        self._background_colour = wx.Colour( r, g, b, a )
        
        ( r, g, b, a ) = text_rgba
        
        self._text_colour = wx.Colour( r, g, b, a )
        
        self._namespace_info = [ tuple( row ) for row in self._namespace_info ]
        
        self._UpdateNamespaceLookup()
        
    
    def _UpdateNamespaceLookup( self ):
        
        self._interesting_namespaces = { namespace for ( namespace, prefix, separator ) in self._namespace_info }
        
    
    def _UpdateSerialisableInfo( self, version, old_serialisable_info ):
        
        if version == 1:
            
            ( namespace_info, separator, example_tags ) = old_serialisable_info
            
            background_rgba = ( 223, 227, 230, 255 )
            text_rgba = ( 1, 17, 26, 255 )
            show = True
            
            new_serialisable_info = ( background_rgba, text_rgba, namespace_info, separator, example_tags, show )
            
            return ( 2, new_serialisable_info )
            
        
    
    def GenerateExampleSummary( self ):
        
        if not self._show:
            
            return 'not showing'
            
        else:
            
            return self.GenerateSummary( self._example_tags )
            
        
    
    def GenerateSummary( self, tags, max_length = None ):
        
        if not self._show:
            
            return ''
            
        
        namespaces_to_subtags = collections.defaultdict( list )
        
        for tag in tags:
            
            ( namespace, subtag ) = HydrusTags.SplitTag( tag )
            
            if namespace in self._interesting_namespaces:
                
                namespaces_to_subtags[ namespace ].append( subtag )
                
            
        
        for ( namespace, unsorted_l ) in list( namespaces_to_subtags.items() ):
            
            sorted_l = HydrusTags.SortNumericTags( unsorted_l )
            
            sorted_l = HydrusTags.CollapseMultipleSortedNumericTagsToMinMax( sorted_l )
            
            namespaces_to_subtags[ namespace ] = sorted_l
            
        
        namespace_texts = []
        
        for ( namespace, prefix, separator ) in self._namespace_info:
            
            subtags = namespaces_to_subtags[ namespace ]
            
            if len( subtags ) > 0:
                
                namespace_text = prefix + separator.join( namespaces_to_subtags[ namespace ] )
                
                namespace_texts.append( namespace_text )
                
            
        
        summary = self._separator.join( namespace_texts )
        
        if max_length is not None:
            
            summary = summary[:max_length]
            
        
        return summary
        
    
    def GetBackgroundColour( self ):
        
        return self._background_colour
        
    
    def GetTextColour( self ):
        
        return self._text_colour
        
    
    def ToTuple( self ):
        
        return ( self._background_colour, self._text_colour, self._namespace_info, self._separator, self._example_tags, self._show )
        
    
HydrusSerialisable.SERIALISABLE_TYPES_TO_OBJECT_TYPES[ HydrusSerialisable.SERIALISABLE_TYPE_TAG_SUMMARY_GENERATOR ] = TagSummaryGenerator
