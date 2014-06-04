#!/usr/bin/python
# Copyright (c) 2014, Red Hat, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the Red Hat nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors:  Michal Srb <msrb@redhat.com>

import sys

from dependency import Dependency
from artifact import AbstractArtifact, ArtifactFormatException
from pomreader import POMReader

from lxml.etree import Element


class Plugin(AbstractArtifact):

    def __init__(self, groupId, artifactId, version="", dependencies=[]):
        self.groupId = groupId.strip() or "org.apache.maven.plugins"
        self.artifactId = artifactId.strip()
        self.version = version.strip()
        self.dependencies = dependencies

    def __unicode__(self):
        return u"{gid}:{aid}:{ver}".format(gid=self.groupId,
                                           aid=self.artifactId,
                                           ver=self.version)

    def __str__(self):
        return unicode(self).encode(sys.getfilesystemencoding())

    def get_xml_element(self, root="plugin"):
        """
        Return XML Element node representation of the Plugin
        """
        root = AbstractArtifact.get_xml_element(self, root)

        if self.dependencies:
            dep_root = Element("dependencies")
            for d in self.dependencies:
                dep_root.insert(len(dep_root), d.get_xml_element())
            root.insert(len(root), dep_root)

        return root

    def get_xml_str(self, root="plugin"):
        """
        Return XML formatted string representation of the Exclusion
        """
        return AbstractArtifact.get_xml_str(self, root)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.groupId.__hash__() + \
               self.artifactId.__hash__() + \
               self.version.__hash__()

    @classmethod
    def from_xml_element(cls, xmlnode):
        """
        Create Plugin from xml.etree.ElementTree.Element as contained
        within pom.xml.
        """

        parts = {'groupId': '', 'artifactId': '', 'version': ''}
        parts = POMReader.find_parts(xmlnode, parts)

        if not parts['artifactId']:
            raise ArtifactFormatException(
                "Empty artifactId encountered. "
                "This is a bug, please report it!")

        # dependencies
        depnodes = POMReader.xpath(xmlnode, "./dependencies/dependency")

        deps = []
        for d in [Dependency.from_xml_element(x) for x in depnodes]:
            deps.append(d)

        return cls(parts['groupId'], parts['artifactId'], parts['version'], deps)

    @classmethod
    def from_mvn_str(cls, mvnstr):
        """
        Create Plugin from Maven-style definition

        The string should be in the format of:
           groupId:artifactId
        """
        p = cls.get_parts_from_mvn_str(mvnstr)
        return cls(p['groupId'], p['artifactId'], p['version'])
