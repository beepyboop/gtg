# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2009 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
import gtk
import gobject
import pango
import xml.sax.saxutils as saxutils

from GTG     import _
from GTG.core.task import Task
from GTG.gtk.browser.CellRendererTags import CellRendererTags
from GTG.gtk.liblarch_gtk import TreeView
from GTG.gtk import colors

class TreeviewFactory():

    def __init__(self,requester,config):
        self.req = requester
        self.config = config
        
        
    #############################
    #Functions for tasks columns
    ################################
    def _count_active_subtasks_rec(self, task):
        count = 0
        if task.has_child():
            for tid in task.get_children():
                task = self.req.get_task(tid)
                if task and task.get_status() == Task.STA_ACTIVE:
                    count = count + 1 + self._count_active_subtasks_rec(task)
        return count
    
    def task_bg_color(self,tags,bg):
        if self.config['browser'].get('bg_color_enable',False):
            return colors.background_color(tags,bg)
        else:
            return None
    
    #return an ordered list of tags of a task
    def task_tags_column(self,node):
        tags = node.get_tags()
        tags.sort(key = lambda x: x.get_name())
        return tags
        
    #task title
    def task_title_column(self, node):
        return saxutils.escape(node.get_title())
        
    #task title/label
    def task_label_column(self, node):
        title = saxutils.escape(node.get_title())
        #FIXME
#        color = self.treeview.style.text[gtk.STATE_INSENSITIVE].to_string()
        color = "#F00"
        if node.get_status() == Task.STA_ACTIVE:
            count = self._count_active_subtasks_rec(node)
            if count != 0:
                title += " (%s)" % count
            
            if self.config.has_key("contents_preview_enable"):
            	excerpt = saxutils.escape(node.get_excerpt(lines=1, \
            		strip_tags=True, strip_subtasks=True))
            	title += " <span size='small' color='%s'>%s</span>" \
            		%(color, excerpt) 
        elif node.get_status() == Task.STA_DISMISSED:
            title = "<span color='%s'>%s</span>"%(color, title)
        return title
        
    #task start date
    def task_sdate_column(self,node):
        return node.get_start_date().to_readable_string()
        
    def task_duedate_column(self,node):
        return node.get_due_date().to_readable_string()
        
    def task_cdate_column(self,node):
        return node.get_closed_date().to_readable_string()
        
    #############################
    #Functions for tags columns
    #############################
    def tag_list(self,node):
        #FIXME: we should really use the name instead of the object
        tname = node.get_id()
        return [node]
    
    def tag_name(self,node):
        return node.get_id()
        
    def get_tag_count(self,node):
        tasktree = self.req.get_main_tasks_tree()
        sp_id = node.get_attribute("special")
        if sp_id == "all":
            toreturn = tasktree.get_n_nodes(\
                    withfilters=['no_disabled_tag'],include_transparent=True)
        elif sp_id == "notag":
            toreturn = tasktree.get_n_nodes(\
                            withfilters=['notag'],include_transparent=True)
        elif sp_id == "sep" :
            toreturn = 0
        else:
            tname = node.get_name()
            toreturn = tasktree.get_n_nodes(\
                                withfilters=[tname],include_transparent=True)
        return toreturn

    ############################################
    ######## The Factory #######################
    ############################################
    def tags_treeview(self,tree):
        desc = {}
        
        #Tags color
        col_name = 'color'
        col = {}
        render_tags = CellRendererTags()
        render_tags.set_property('ypad', 3)
        col['title'] = _("Tags")
        col['renderer'] = ['tag_list',render_tags]
        col['value'] = [gobject.TYPE_PYOBJECT,self.tag_list]
        col['expandable'] = False
        col['resizable'] = False
        col['order'] = 1
        desc[col_name] = col
        
        #Tag names
        col_name = 'tagname'
        col = {}
        render_text = gtk.CellRendererText()
        render_text.set_property('editable', True) 
        render_text.set_property('ypad', 3)
        #FIXME : renaming tag feature
        render_text.connect("edited", self.req.rename_tag)
        col['renderer'] = ['markup',render_text]
        col['value'] = [str,self.tag_name]
        col['expandable'] = True
        col['new_column'] = False
        col['order'] = 2
        desc[col_name] = col
        
        #Tag count
        col_name = 'tagcount'
        col = {}
        render_text = gtk.CellRendererText()
        render_text.set_property('xpad', 3)
        render_text.set_property('ypad', 3)
        render_text.set_property("foreground", "#888a85")
        render_text.set_property('xalign', 1.0)
        col['renderer'] = ['markup',render_text]
        col['value'] = [str,self.get_tag_count]
        col['expandable'] = False
        col['new_column'] = False
        col['order'] = 3
        desc[col_name] = col
        
        return self.build_tag_treeview(tree,desc)
    
    def active_tasks_treeview(self,tree):
        #Build the title/label/tags columns
        desc = self.common_desc_for_tasks(tree)
        
        # "startdate" column
        col_name = 'startdate'
        col = {}
        col['title'] = _("Start date")
        render_text = gtk.CellRendererText()
        col['expandable'] = False
        col['renderer'] = ['markup',render_text]
        col['resizable'] = False
        col['value'] = [str,self.task_sdate_column]
        col['order'] = 3
        desc[col_name] = col

        # 'duedate' column
        col_name = 'duedate'
        col = {}
        col['title'] = _("Due")
        render_text = gtk.CellRendererText()
        col['expandable'] = False
        col['renderer'] = ['markup',render_text]
        col['resizable'] = False
        col['value'] = [str,self.task_duedate_column]
        col['order'] = 4
        desc[col_name] = col

        #Returning the treeview
        treeview = self.build_task_treeview(tree,desc)
        return treeview
        
    def closed_tasks_treeview(self,tree):
        #Build the title/label/tags columns
        desc = self.common_desc_for_tasks(tree)
        
        # "startdate" column
        col_name = 'closeddate'
        col = {}
        col['title'] = _("Closed date")
        render_text = gtk.CellRendererText()
        col['expandable'] = False
        col['renderer'] = ['markup',render_text]
        col['resizable'] = False
        col['value'] = [str,self.task_cdate_column]
        col['order'] = 3
        desc[col_name] = col

        #Returning the treeview
        treeview = self.build_task_treeview(tree,desc)
        return treeview
        
    
    def common_desc_for_tasks(self,tree):
        desc = {}
        #invisible 'title' column
        col_name = 'title'
        col = {}
        render_text = gtk.CellRendererText()
        render_text.set_property("ellipsize", pango.ELLIPSIZE_END)
        col['renderer'] = ['markup',render_text]
        col['value'] = [str,self.task_title_column]
        col['visible'] = False
        col['order'] = 0
        desc[col_name] = col
        
        # "tags" column (no title)
        col_name = 'tags'
        col = {}
        render_tags = CellRendererTags()
        render_tags.set_property('xalign', 0.0)
        col['renderer'] = ['tag_list',render_tags]
        col['value'] = [gobject.TYPE_PYOBJECT,self.task_tags_column]
        col['expandable'] = False
        col['resizable'] = False
        col['order'] = 1
        desc[col_name] = col

        # "label" column
        col_name = 'label'
        col = {}
        col['title'] = _("Title")
        render_text = gtk.CellRendererText()
        render_text.set_property("ellipsize", pango.ELLIPSIZE_END)
        col['renderer'] = ['markup',render_text]
        col['value'] = [str,self.task_label_column]
        col['expandable'] = True
        col['resizable'] = True
        col['sorting'] = 'title'
        col['order'] = 2
        desc[col_name] = col
        return desc
        
    def build_task_treeview(self,tree,desc):
        treeview = TreeView(tree,desc)
        #Now that the treeview is done, we can polish
        treeview.set_main_search_column('label')
        treeview.set_expander_column('label')
        #Background colors
        treeview.set_bg_color(self.task_bg_color,'tags')
         # Global treeview properties
        treeview.set_property("enable-tree-lines", False)
        treeview.set_rules_hint(False)
        return treeview
        
    def build_tag_treeview(self,tree,desc):
        treeview = TreeView(tree,desc)
        # Global treeview properties
        treeview.set_property("enable-tree-lines", False)
        treeview.set_rules_hint(False)
        return treeview
        
        
        #TODO
        #This code was in the old tasktree and I'm not sure liblarch-gtk
        #already implement those features 
#        self.task_modelsort.set_sort_func(\
#            tasktree.COL_DDATE, self.date_sort_func)
#        self.task_modelsort.set_sort_func(\
#            tasktree.COL_DLEFT, self.date_sort_func)
# Connect signals from models
#        self.task_modelsort.connect("row-has-child-toggled",\
#                                    self.on_task_child_toggled)
# Set sorting order
#        self.task_modelsort.set_sort_column_id(\
#            tasktree.COL_DLEFT, gtk.SORT_ASCENDING)
        
