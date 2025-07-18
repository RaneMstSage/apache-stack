#!/usr/bin/env python3
"""
Repository Access Configuration Loader
Loads and parses repository access control from .conf configuration
"""

import os
import logging
import configparser

logger = logging.getLogger(__name__)

class RepoAccessConfig:
    def __init__(self, config_file='/opt/config/repo-access.conf'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Load configuration from .conf file"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                logger.info(f"Loaded repository access config from {self.config_file}")
            else:
                logger.warning(f"Config file not found: {self.config_file}, using defaults")
                self._set_defaults()
        except Exception as e:
            logger.error(f"Error loading config file {self.config_file}: {e}")
            self._set_defaults()
    
    def _set_defaults(self):
        """Set default configuration if file is not available"""
        self.config.add_section('defaults.git')
        self.config.set('defaults.git', 'read_groups', 'git-users,admins')
        self.config.set('defaults.git', 'write_groups', 'git-users,admins')
        
        self.config.add_section('defaults.svn')
        self.config.set('defaults.svn', 'read_groups', 'svn-users,admins')
        self.config.set('defaults.svn', 'write_groups', 'svn-users,admins')
    
    def get_git_access_groups(self, repo_name, username, is_write=False):
        """Get required LDAP groups for Git repository access"""
        section = f'git.{repo_name}'
        
        if self.config.has_section(section):
            # Check if user is the owner of a personal repository
            if self.config.has_option(section, 'owner'):
                owner = self.config.get(section, 'owner')
                if owner == username:
                    logger.info(f"Personal repository access granted for owner '{username}'")
                    return []  # Owner has access, no group check needed
        
            # Check if repository has specific groups
            if self.config.has_option(section, 'groups'):
                groups = self.config.get(section, 'groups').split(',')
                return [g.strip() for g in groups]
            
            # Check admin groups for personal repos
            if self.config.has_option(section, 'admin_groups'):
                groups = self.config.get(section, 'admin_groups').split(',')
                return [g.strip() for g in groups]
    
        # Use defaults - simpler groups
        default_section = 'defaults.git'
        if self.config.has_option(default_section, 'read_groups'):
            groups = self.config.get(default_section, 'read_groups').split(',')
        else:
            groups = ['git-users', 'admins']  # Simple default
        
        return [g.strip() for g in groups]
    
    def get_svn_access_groups(self, repo_path, username, is_write=False):
        """Get required LDAP groups for SVN repository access"""
        if not repo_path:
            # Use defaults if no path specified
            default_section = 'defaults.svn'
            if self.config.has_option(default_section, 'read_groups'):
                groups = self.config.get(default_section, 'read_groups').split(',')
            else:
                groups = ['svn-users', 'admins']  # Simple default
            return [g.strip() for g in groups]
        
        # Extract collection name from path
        path_parts = repo_path.strip('/').split('/')
        collection_name = path_parts[0] if path_parts else None
        
        if collection_name:
            section = f'svn.{collection_name}'
            
            if self.config.has_section(section):
                # Check if user is the owner of a personal collection
                if self.config.has_option(section, 'owner'):
                    owner = self.config.get(section, 'owner')
                    if owner == username:
                        logger.info(f"Personal collection access granted for owner '{username}'")
                        return []  # Owner has access, no group check needed
                
                # Check if collection has specific groups
                if self.config.has_option(section, 'groups'):
                    groups = self.config.get(section, 'groups').split(',')
                    return [g.strip() for g in groups]
                
                # Check admin groups for personal collections
                if self.config.has_option(section, 'admin_groups'):
                    groups = self.config.get(section, 'admin_groups').split(',')
                    return [g.strip() for g in groups]
    
        # Use defaults - simpler groups  
        default_section = 'defaults.svn'
        if self.config.has_option(default_section, 'read_groups'):
            groups = self.config.get(default_section, 'read_groups').split(',')
        else:
            groups = ['svn-users', 'admins']  # Simple default
        
        return [g.strip() for g in groups]

# Global instance
_config_instance = None

def get_repo_config():
    """Get the global repository configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = RepoAccessConfig()
    return _config_instance

def reload_config():
    """Reload the configuration from file"""
    global _config_instance
    _config_instance = RepoAccessConfig()
    return _config_instance