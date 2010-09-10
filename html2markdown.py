#!/usr/bin/python
#
# html2markdown
# Copyright 2005 Dale Sedivec
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# XXX
# TODO:
# * Change constant names to upper case.
# * Test wrapping of HTML in Markdown source with long attributes that
#   have whitespace in their contents.
# * Should probably put non-breaking spaces in the middle of a
#   Markdown image markup.
# * Stop all the interpolation and concatenation operations and take
#   advantage of buffers more (use write not +)
# * In code, do a consistency check WRT indentation on continued
#   statements.
# * Look at inline HTML in indented block elements (block quote, list,
#   maybe code block)
# * Test CLI.
# * Check through for classes that are too big (refactoring)
# * Write test for <li>[whitespace]<p>...</p></li>.  I'm not sure that
#   Markdown will ever generate this, but it still looks likely to
#   happen in hand-written HTML.
# * Make test with numeric entity to make sure handle_charref is
#   implemented.
# * It's possible that (almost) everywhere we do an isinstance()
#   check, we should really be doing some kind of hasFeature() check,
#   hasFeature() being a method we implement?  More flexible.

from HTMLParser import HTMLParser
from StringIO import StringIO
import logging
import textwrap
import re
import string
import inspect
import sys
from itertools import repeat, chain

WRAP_AT_COLUMN = 70
# XXX This is kind of dumb, really, since certain types of syntax
# demand certain types of indents.  To parameterize this, we should
# probably find all indent instances, change them to this variable,
# then see what breaks with one indent or the other and hard code that
# particular indent.
MARKDOWN_INDENT = "    "

log = logging.getLogger("html2markdown")

try:
    any
except NameError:
    def any(items):
        for item in items:
            if item:
                return True
        return False

    def all(items):
        for item in items:
            if not item:
                return False
        return True

# XXX TEST this is not tested?  Plus it probably doesn't belong here.
# At least document it.
# def getMyCaller(): #pragma: no cover
#     try:
#         callerFrame = inspect.getouterframes(inspect.currentframe())[2]
#         return "%s:%d" % (callerFrame[3], callerFrame[2])
#     finally:
#         del callerFrame


class Box (object):
    def __init__(self):
        self.parent = None

    def render(self, writer):
        raise NotImplementedError("you must overload this") #pragma: no cover

    width = property(fget=lambda self: self.parent.width)

class ContainerBox (Box):
    def __init__(self):
        super(ContainerBox, self).__init__()
        self.children = []

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

    def makeChild(self, childClass):
        child = childClass()
        self.addChild(child)
        return child

class CompositeBox (ContainerBox):
    def __init__(self, addNewLines=True):
        super(CompositeBox, self).__init__()
        self.__addNewLineAfterChild = []
        self.__addNewLines = addNewLines

    def addChild(self, child):
        super(CompositeBox, self).addChild(child)
        self.__addNewLineAfterChild.append(self.__addNewLines)

    def insertNewLineAfterChild(self, childIndex):
        assert childIndex >= 0, childIndex
        self.__addNewLineAfterChild[childIndex] = True

    def insertNewLineBeforeLastChild(self):
        self.__addNewLineAfterChild[-2] = True

    def render(self, writer):
        if self.children:
            assert len(self.__addNewLineAfterChild) == len(self.children)
            addNewLine = iter(self.__addNewLineAfterChild)
            self.children[0].render(writer)
            for child in self.children[1:]:
                if addNewLine.next():
                    writer("\n")
                child.render(writer)

class RootBox (CompositeBox):
    # Override the property set in a superclass.  (XXX Is this the
    # cleanest way to do this?)
    width = None

    def __init__(self, width):
        super(RootBox, self).__init__()
        self.width = width

def ijoin(iterable, joinString):
    """Yields joinString between items from iterable.

    s.join(i) == "".join(ijoin(i, s))

    """
    iterator = iter(iterable)
    yield iterator.next()
    for item in iterator:
        yield joinString
        yield item

class TextBox (Box):
    def __init__(self):
        self.__lines = [StringIO()]

    def addText(self, text):
        self.__lines[-1].write(text)

    def addLineBreak(self):
        self.__lines.append(StringIO())

    def _iterLines(self):
        for line in self.__lines:
            yield line.getvalue()

    def render(self, writer):
        for string in ijoin(self._iterLines(), "  \n"):
            writer(string)
        if string[-1] != "\n":
            writer("\n")

class iterAllButLast (object):
    def __init__(self, iterable):
        self._iterator = iter(iterable)

    def __iter__(self):
        lastItem = self._iterator.next()
        for item in self._iterator:
            yield lastItem
            lastItem = item
        self.last = lastItem

class WrappedTextBox (TextBox):
    __wordBoundaryRegexp = re.compile(r'(\s+)')

    def render(self, writer):
        def fill(line, lastLineSuffix=""):
            return self.__fill(line, self.width, lastLineSuffix, writer)

        lines = iterAllButLast(self._iterLines())
        for line in lines:
            writer(fill(line, "  "))
        writer(fill(lines.last))

    # XXX REFACTOR I'd say refactor this, but right now I don't see a
    # particularly clean way to do it.
    #
    # There should be a way, though.  All this code seems so verbose,
    # if not needlessly complex.
    def __fill(self, text, width, lastLineSuffix, writer):
        log.debug("fill text=%r suffix=%r" % (text, lastLineSuffix))
        words = self.__splitTextIntoWordsAndSpaces(text)
        firstSpace, firstWord = words.pop(0)
        linePosition = self.__writeFirstWordOnLine(firstWord, writer)
        for spaceBefore, word in words:
            spaceLen = len(spaceBefore)
            wordLen = len(word)
            if (linePosition + spaceLen + wordLen) > width:
                writer("\n")
                self.__writeFirstWordOnLine(word, writer)
                linePosition = wordLen
            else:
                writer(spaceBefore)
                writer(word)
                linePosition += spaceLen + wordLen
        writer(lastLineSuffix)
        writer("\n")

    # The second grouping prevents **strong** from tripping this
    # regular expression.
    __beginningOfLineTokens = re.compile(r"^([0-9]+\.|[*+-]([^*]|$)|#)")

    def __writeFirstWordOnLine(self, word, writer):
        """Writes the first word using writer, adding escaping if needed.

        Markdown assigns special meaning to certain tokens when they
        appear at the beginning of a line.  We have to esacpe these
        special characters if they happen to appear at the beginning
        of a line after a paragraph is wrapped.  This function will
        return the total number of characters written, which might be
        bigger than len(word) if an escape character is added.

        """
        wordLen = len(word)
        tokenMatch = self.__beginningOfLineTokens.search(word)
        if tokenMatch:
            matchEndPosition = tokenMatch.end(1)
            log.debug("word=%r matchEndPosition=%r" % (word, matchEndPosition))
            writer(word[0:matchEndPosition - 1])
            writer("\\")
            writer(word[matchEndPosition - 1:])
            return wordLen + 1
        else:
            log.debug("word=%r no match" % (word,));
            writer(word)
            return wordLen

    def __splitTextIntoWordsAndSpaces(self, text):
        """

        Builds and returns a list of tuples in the form (space
        before word, word), where the spaces and words are determined
        by splitting text on word boundaries.  This is used primarily
        by the fill() method.

        """
        log.debug("splitTextIntoWordsAndSpaces: text=%r" % (text,))
        parts = self.__wordBoundaryRegexp.split(text)
        log.debug("splitTextIntoWordsAndSpaces: normalizing %r" % (parts,))
        self.__normalizeSplitTextParts(parts)
        log.debug("splitTextIntoWordsAndSpaces: after normalizing %r"
                  % (parts,))
        words = []
        lastWord = ""
        for spaceBefore, word in zip(parts[::2], parts[1::2]):
            spaceBefore = self.__normalizeWordSpacing(spaceBefore, lastWord)
            words.append((spaceBefore, word))
            lastWord = word
        return words

    def __normalizeWordSpacing(self, spaceBefore, precedingWord):
        # If the input is "foo.\nbar" you'll end up with "foo. bar"
        # even if you separate your sentences with two spaces.  I'm
        # not inclined to do anything to fix this until someone really
        # bitches about it.  Also, two spaces are "safer" than one in
        # the case of (for example) "Mr.\nSmith".
        if spaceBefore[0:2] == "  " and precedingWord[-1] in ".?!:":
            spaceBefore = "  "
        else:
            spaceBefore = " "
        return spaceBefore

    def __normalizeSplitTextParts(self, parts):
        """

        This method makes sure that the parts list is a list of space,
        word, space, word, space, word, ...  The first element in the
        list will always be the empty string (an empty space).

        This method is used by the wrapping code.

        """
        if parts[0] == "":
            del parts[1]
        else:
            parts.insert(0, "")
        if parts[-1] == "":
            del parts[-2:]
        assert (len(parts) % 2) == 0, "List normalizing failed: %r" % (parts,)

class IndentedBox (ContainerBox):
    def __init__(self, indent, firstLineIndent=None):
        super(IndentedBox, self).__init__()
        self.__indentLength = len(indent)
        self.__subsequentLineIndent = indent
        if firstLineIndent is not None:
            assert len(firstLineIndent) == self.__indentLength
            self.__firstLineIndent = firstLineIndent
        else:
            self.__firstLineIndent = indent

    def render(self, writer):
        childRendering = StringIO()
        self.__renderChildren(childRendering.write)
        self.__rewindFile(childRendering)
        self.__renderLinesFromFile(childRendering, writer)

    def __renderLinesFromFile(self, childRendering, writer):
        indentGenerator = chain([self.__firstLineIndent],
                                repeat(self.__subsequentLineIndent))
        for line in childRendering:
            indent = indentGenerator.next()
            if self.__isBlankLine(line):
                indent = indent.rstrip()
            writer(indent)
            writer(line)

    def __isBlankLine(self, line):
        return not line.rstrip("\r\n")

    def __rewindFile(self, childRendering):
        childRendering.seek(0)

    def __renderChildren(self, writer):
        for child in self.children:
            child.render(writer)

    def _getWidth(self):
        return super(IndentedBox, self).width - self.__indentLength
    width = property(fget=_getWidth)

class RawTextBox (TextBox):
    """A TextBox whose contents shouldn't have Markdown elements escaped."""
    pass

# Based on DOM.  Should probably refer to this as MDDOM (Markdown
# DOM).  I think I used "micro-DOM" somewhere else.
class Node (object):
    def __init__(self):
        self.parent = None

class ContainerNode (Node):
    def __init__(self):
        super(ContainerNode, self).__init__()
        self.children = []

    def makeChild(self, type):
        child = type()
        self.addChild(child)
        return child

    def addChild(self, child):
        self.children.append(child)
        child.parent = self

# An InlineNode is a Node that does not render to a Box, but rather
# modifies the Box inside which it occurs.  Currently this is used to
# mark Nodes whose transformation requires a Box that supports
# addText().
class InlineNode (Node):
    pass

# A TextContainer is a ContainerNode that may also hold
# TextRelatedNodes.  The HTML parser will ignore text that occurs
# outside of a TextContainer.
class TextContainer (ContainerNode):
    pass

class InlineTextContainer (InlineNode, TextContainer):
    pass

class Text (InlineNode):
    def __init__(self, text=""):
        super(Node, self).__init__()
        self.text = text

class Document (ContainerNode):
    pass

class List (ContainerNode):
    pass

class OrderedList (List):
    def getChildIndex(self, child):
        return self.children.index(child)

class UnorderedList (List):
    pass

class ListItem (TextContainer):
    def getItemNumber(self):
        # This method is only valid when this is an item in an
        # OrderedList.  Obviously.
        return self.parent.getChildIndex(self) + 1

class BlockQuote (ContainerNode):
    pass

class Paragraph (TextContainer):
    pass

class Preformatted (TextContainer):
    pass

class HTML (TextContainer):
    pass

class Code (InlineTextContainer):
    pass

class Emphasized (InlineTextContainer):
    pass

class Strong (InlineTextContainer):
    pass

class LineBreak (InlineNode):
    pass

class Image (InlineNode):
    def __init__(self, url, alternateText=None, title=None):
        super(Image, self).__init__()
        self.url = url
        self.alternateText = alternateText
        self.title = title

class Heading (TextContainer):
    def __init__(self, level):
        super(Heading, self).__init__()
        self.level = level

class HorizontalRule (Node):
    pass

class Anchor (InlineTextContainer):
    def __init__(self, url, title=None):
        super(Anchor, self).__init__()
        self.url = url
        self.title = title

class UnknownInlineElement (InlineTextContainer):
    def __init__(self, tag, attributes):
        super(UnknownInlineElement, self).__init__()
        self.tag = tag
        self.attributes = attributes


class MarkdownTransformer (object):
    __formattingCharactersRegexp = re.compile(r"((?<=\S)([*_])|([*_])(?=\S))")

    def transform(self, document):
        rootBox = RootBox(width=WRAP_AT_COLUMN)
        self.__dispatchChildren(document, rootBox)
        return rootBox

    def __dispatch(self, node, parentBox):
        log.debug("Dispatching node=%r parentBox=%r" % (node, parentBox))
        if isinstance(node, List):
            nodeTypeName = "List"
        else:
            nodeTypeName = type(node).__name__
        getattr(self, "_transform" + nodeTypeName)(node, parentBox)
        # self.__handlers[type(node)](self, node, parentBox)

    def __dispatchChildren(self, node, parentBox):
        self.__dispatchList(node.children, parentBox)

    def __dispatchList(self, nodeList, parentBox):
        for node in nodeList:
            self.__dispatch(node, parentBox)

    def _transformParagraph(self, node, parentBox):
        box = parentBox.makeChild(WrappedTextBox)
        self.__dispatchChildren(node, box)

    def _transformBlockQuote(self, node, parentBox):
        indentedBox = IndentedBox(indent="> ")
        parentBox.addChild(indentedBox)
        dividedBox = indentedBox.makeChild(CompositeBox)
        self.__dispatchChildren(node, dividedBox)

    def _transformPreformatted(self, node, parentBox):
        indentedBox = IndentedBox(indent=MARKDOWN_INDENT)
        parentBox.addChild(indentedBox)
        textBox = indentedBox.makeChild(TextBox)
        self.__dispatchChildren(node, textBox)

    def _transformText(self, node, parentBox):
        if isinstance(node.parent, (HTML, Preformatted, Code)) \
           or isinstance(parentBox, RawTextBox):
            text = node.text
        else:
            text = self.__escapeFormattingCharacters(node.text)
        parentBox.addText(text)

    def __escapeFormattingCharacters(self, data):
        escapedData = data.replace("\\", "\\\\")
        escapedData = self.__formattingCharactersRegexp.sub(r"\\\1",
                                                            escapedData)
        return escapedData

    def _transformList(self, node, parentBox):
        box = CompositeBox(addNewLines=False)
        parentBox.addChild(box)
        self.__dispatchChildren(node, box)
        self.__addExplicitParagraphsInList(node, box)

    # XXX REFACTOR if you dare.  The list code (here and ListItem
    # processing) is nigh incomprehensible.  Of course, I can't even
    # figure out how to simplify this function since the way it
    # figures out where to put explicit paragraphs is so arcane (and
    # the rules for how to generate <p></p> are, shall we say,
    # "tedious").
    def __addExplicitParagraphsInList(self, node, box):
        paragraphAnalysis = []
        for listItem in node.children:
            isSingleParagraph = False
            if isinstance(listItem.children[0], Paragraph):
                isSingleParagraph = True
                for child in listItem.children[1:]:
                    if isinstance(child, List):
                        break
                    elif not isinstance(child, Text):
                        isSingleParagraph = False
                        break
            paragraphAnalysis.append(isSingleParagraph)
        log.debug("paragraphAnalysis=%r" % (paragraphAnalysis,))
        
        consecutiveSingleParas = 0
        for childIndex, isSingleParagraph in enumerate(paragraphAnalysis):
            if isSingleParagraph:
                consecutiveSingleParas += 1
                if consecutiveSingleParas >= 2:
                    box.insertNewLineAfterChild(childIndex - 1)
            else:
                if consecutiveSingleParas == 1:
                    if any([ isinstance(n, List) for n
                             in node.children[childIndex - 1].children ]):
                        # A List node's children can only be
                        # ListItems, and a ListItem always generates
                        # an outer CompositeBox, so box.children are
                        # all CompositeBoxes.
                        box.children[childIndex - 1].insertNewLineAfterChild(0)
                    else:
                        box.insertNewLineBeforeLastChild()
                consecutiveSingleParas = 0
        # XXX Near exact copy of above code.
        if consecutiveSingleParas == 1:
            if any([ isinstance(n, List) for n
                     in node.children[childIndex].children ]):
                box.children[childIndex].insertNewLineAfterChild(0)
            else:
                box.insertNewLineBeforeLastChild()

    # XXX REFACTOR
    def _transformListItem(self, node, parentBox):
        BOX_AT_BULLET_LEVEL = 1
        BOX_AT_LIST_ITEM_LEVEL = 2

        outerBox = CompositeBox(addNewLines=False)
        parentBox.addChild(outerBox)
        # XXX This code to determine indents will have a tendency to
        # not work right if you want to make MARKDOWN_INDENT = "\t"
        # (for example).
        bulletIndent = "    "
        if isinstance(node.parent, OrderedList):
            number = "%d. " % (node.getItemNumber(),)
            number = number + " " * (4 - len(number))
            # XXX Should we use len(number) instead of 4 here?  Are
            # more than four spaces on continued lines fine with
            # Markdown?
            indentedBox = IndentedBox(firstLineIndent=number,
                                      indent=bulletIndent)
        else:
            indentedBox = IndentedBox(firstLineIndent="*   ",
                                      indent=bulletIndent)
        outerBox.addChild(indentedBox)
        innerBox = indentedBox.makeChild(CompositeBox)

        children = node.children[:]
        # The first child has to be in the indent box that has the
        # list bullet.
        if isinstance(children[0], InlineNode):
            # A ListItem that starts with text can only have text or
            # nested lists under it.  I think.
            log.debug("List item dispatching text children")
            textBox = innerBox.makeChild(WrappedTextBox)
            while children and isinstance(children[0], InlineNode):
                self.__dispatch(children.pop(0), textBox)
        elif isinstance(children[0], List):
            # Immediate sublist.
            listIndentBox = IndentedBox(indent=MARKDOWN_INDENT)
            innerBox.addChild(listIndentBox)
            self.__dispatch(children.pop(0), listIndentBox)
        else:
            self.__dispatch(children.pop(0), innerBox)

        innerBoxType = BOX_AT_BULLET_LEVEL
        for child in children:
            if isinstance(child, Text):
                # Ignore whitespace that occurs between elements.
                continue
            elif isinstance(child, (Preformatted, List)):
                if innerBoxType != BOX_AT_LIST_ITEM_LEVEL:
                    innerBox = IndentedBox(indent=MARKDOWN_INDENT)
                    outerBox.addChild(innerBox)
                    if isinstance(child, Preformatted):
                        outerBox.insertNewLineBeforeLastChild()
                    innerBoxType = BOX_AT_LIST_ITEM_LEVEL
            else:
                if innerBoxType != BOX_AT_BULLET_LEVEL:
                    indentedBox = IndentedBox(indent=bulletIndent)
                    outerBox.addChild(indentedBox)
                    outerBox.insertNewLineBeforeLastChild()
                    innerBox = indentedBox.makeChild(CompositeBox)
                    innerBoxType = BOX_AT_BULLET_LEVEL
            self.__dispatch(child, innerBox)

    # XXX Might want to factor out this pattern.
    def _transformHTML(self, node, parentBox):
        box = parentBox.makeChild(TextBox)
        self.__dispatchChildren(node, box)

    __backtickRegexp = re.compile("`+")

    def _transformCode(self, node, parentBox):
        contents = self.__renderChildren(node)
        codeDelimiter = self.__makeCodeDelimiter(contents)
        parentBox.addText(codeDelimiter)
        if contents[0] == "`":
            parentBox.addText(" ")
        parentBox.addText(contents)
        if contents[-1] == "`":
            parentBox.addText(" ")
        parentBox.addText(codeDelimiter)

    def __makeCodeDelimiter(self, content):
        """Returns the correct number of backticks to set off string as code.

        Markdown requires you to use at least one more backtick to
        introduce/conclude a code span than there are backticks within
        the code span.  For example, if contents="foo ``date`` bar",
        Markdown would require ``` to be used to begin/end the code
        span for that string.

        """
        matches = self.__backtickRegexp.findall(content)
        if matches:
            codeDelimiterLength = max([ len(m) for m in matches ]) + 1
        else:
            codeDelimiterLength = 1
        return "`" * codeDelimiterLength

    def _transformEmphasized(self, node, parentBox):
        parentBox.addText("_")
        self.__dispatchChildren(node, parentBox)
        parentBox.addText("_")

    def _transformLineBreak(self, node, parentBox):
        parentBox.addLineBreak()

    def _transformImage(self, node, parentBox):
        parentBox.addText("![")
        parentBox.addText(node.alternateText)
        parentBox.addText("](")
        parentBox.addText(node.url)
        if node.title:
            parentBox.addText(' "')
            parentBox.addText(node.title)
            parentBox.addText('"')
        parentBox.addText(")")

    def _transformHeading(self, node, parentBox):
        box = parentBox.makeChild(TextBox)
        box.addText("#" * node.level + " ")
        self.__dispatchChildren(node, box)
        box.addText(" " + node.level * "#")

    def _transformHorizontalRule(self, node, parentBox):
        box = parentBox.makeChild(TextBox)
        box.addText("---")

    def _transformAnchor(self, node, parentBox):
        # Sometimes this renders the contents twice: once as "raw
        # text" (no escaping of formatting characters) so we can match
        # a URL that might have Markdown formatting characters in it
        # (f.e. http://example.com/foo_bar_baz), and the second time
        # with Markdown escaping if the contents aren't the same as
        # the href.
        linkContents = self.__renderChildren(node, boxType=RawTextBox)
        url = node.url
        isMailto = url.startswith("mailto:")
        if linkContents == url or (isMailto and linkContents == url[7:]):
            parentBox.addText("<")
            parentBox.addText(linkContents)
            parentBox.addText(">")
        else:
            parentBox.addText("[")
            parentBox.addText(self.__renderChildren(node))
            parentBox.addText("](")
            parentBox.addText(url)
            if node.title:
                parentBox.addText(' "')
                parentBox.addText(node.title)
                parentBox.addText('"')
            parentBox.addText(")")

    def __renderChildren(self, node, boxType=TextBox):
        textBox = boxType()
        self.__dispatchChildren(node, textBox)
        contents = StringIO()
        textBox.render(contents.write)
        return contents.getvalue().strip()

    def _transformStrong(self, node, parentBox):
        parentBox.addText("**")
        self.__dispatchChildren(node, parentBox)
        parentBox.addText("**")

    def _transformUnknownInlineElement(self, node, parentBox):
        write = parentBox.addText
        write("<")
        write(node.tag)
        for name, value in node.attributes:
            if '"' in value:
                quotingChar = "'"
            else:
                quotingChar = '"'
            write(" ")
            write(name)
            write('=')
            write(quotingChar)
            write(value)
            write(quotingChar)
        if node.children:
            write(">")
            self.__dispatchChildren(node, parentBox)
            write("</")
            write(node.tag)
            write(">")
        else:
            write(" />")


# XXX TEST Should test this?
class LineNumberedBuffer (StringIO):
    __eolRegexp = re.compile(r"(\r?\n)")

    def __init__(self):
        StringIO.__init__(self)
        self.__linePositions = [0]

    def write(self, string):
        parts = self.__eolRegexp.split(string)
        log.debug("LineNumberedBuffer write split parts=%r" % (parts,))
        for part in parts:
            StringIO.write(self, part)
            if "\n" in part:
                log.debug("new line at %d" % (self.tell(),))
                self.__linePositions.append(self.tell())
        log.debug("LineNumberedBuffer.write final pos=%d" % (self.tell(),))

    def seekLinePosition(self, lineNumber, offset):
        """Seek to an offset from the start of line lineNumber.

        The first line is 1, the first character on a line is 0.  This
        is in line with HTMLParser.getpos().

        """
        position = self.__linePositions[lineNumber - 1] + offset
        log.debug("seekLinePosition (%d,%d)=%d" % (lineNumber, offset,
                                                   position))
        self.seek(position, 0)
        log.debug("seekLinePosition tell=%d" % (self.tell(),))
        assert self.tell() == position, "seekLinePosition failed"

# XXX Turn this into MDDOMParser, outputs MDDOM?  Then you take the
# Document and ship it off to MarkdownTransformer.  Should at least
# give this class a better name.
class MarkdownTranslator (HTMLParser):
    __translatedEntities = {"amp": "&",
                            "lt": "<",
                            "gt": ">",
                            "quot": '"'}

    __unsupportedBlockElements = ("dl", "div", "noscript", "form", "table",
                                  "fieldset", "address")

    def reset(self):
        HTMLParser.reset(self)
        self.__shouldOutputStack = [False]
        self.__unsupportedElementDepth = 0
        self.__unsupportedBlockStart = None
        self.__input = LineNumberedBuffer()
        self.__currentNode = Document()

    def feed(self, text):
        self.__input.write(text)
        HTMLParser.feed(self, text)

    def handle_starttag(self, tag, attrs):
        if self.__unsupportedElementDepth:
            self.__unsupportedElementDepth += 1
        elif tag == "code" \
                 and isinstance(self.__currentNode,
                                Preformatted) \
                 and len(self.__currentNode.children) == 0:
            # Special case: ignore <code> immediately following <pre>.
            # Markdown emits <pre><code>...</code></pre> for a
            # preformatted text block.
            #
            # XXX In the interest of moving to just a DOM HTML parser,
            # I think I support moving this logic to
            # MarkdownTransformer.
            pass
        else:
            # XXX REFACTOR
            element = None
            handler = self.__recognizedTags.get(tag)
            if handler:
                if not isinstance(handler, type):
                    element = handler(self, tag, attrs)
                    isBlock = handler.isBlock
                elif attrs:
                    isBlock = not issubclass(handler, InlineNode)
                else:
                    element = self.__currentNode.makeChild(handler)
            else:
                isBlock = tag in self.__unsupportedBlockElements
            if not element and not isBlock:
                element = UnknownInlineElement(tag, attrs)
                self.__currentNode.addChild(element)
            if element:
                self.__currentNode = element
                self.__shouldOutputStack.append(isinstance(element,
                                                           TextContainer))
            else:
                self.__enterUnsupportedBlockElement()

    def handle_endtag(self, tag):
        log.debug("Leaving tag=%r" % (tag,))
        if self.__unsupportedElementDepth:
            log.debug("Leaving unsupported element")
            self.__leaveUnsupportedElement()
        elif tag == "code" and isinstance(self.__currentNode,
                                          Preformatted):
            # Special case for </code></pre>.  See similar exception
            # in handle_starttag() for explanation.
            pass
        else:
            log.debug("Leaving element")
            self.__leaveElement()

    def __enterUnsupportedBlockElement(self):
        self.__unsupportedElementDepth = 1
        self.__unsupportedBlockStart = self.getpos()

    # XXX REFACTOR
    def __leaveUnsupportedElement(self):
        self.__unsupportedElementDepth -= 1
        log.debug("unsupportedBlockDepth=%r"
                  % (self.__unsupportedElementDepth,))
        if not self.__unsupportedElementDepth:
            log.debug("Finished with unsupported block element");
            log.debug("positions begin=%r end=%r"
                      % (self.__unsupportedBlockStart, self.getpos()))
            html = self.__getUnsupportedBlockElementHTML()
            htmlNode = self.__currentNode.makeChild(HTML)
            htmlNode.addChild(Text(html))
            self.__positionInputBufferAtEnd()

    # XXX Maybe refactor -- or rename to something shorter (applies to
    # all methods following this naming convention).
    def __getUnsupportedBlockElementHTML(self):
        """Side effect: repositions self.__input."""
        endPosition = self.__getEndOfTagPosition(self.getpos())
        self.__input.seekLinePosition(*self.__unsupportedBlockStart)
        startPosition = self.__input.tell()
        htmlLength = endPosition - startPosition
        log.debug("endPosition=%d startPosition=%d len=%d"
                  % (endPosition, startPosition, htmlLength))
        html = StringIO()
        html.write(self.__input.read(htmlLength))
        html.write("\n")
        return html.getvalue()

    def __getEndOfTagPosition(self, startAt):
        """Side effect: repositions self.__input."""
        self.__input.seekLinePosition(*startAt)
        self.__searchInputForTagClose()
        return self.__input.tell()

    def __searchInputForTagClose(self):
        # XXX expensive debugging statement
        log.debug("searchInputForTagClose pos=%d input=%r"
                  % (self.__input.tell(),
                     self.__input.getvalue()))
        while True:
            nextCharacter = self.__input.read(1)
            if not nextCharacter:
                assert False, "premature tag end in input"  #pragma: no cover
            elif nextCharacter == ">":
                break

    def __positionInputBufferAtEnd(self):
        self.__input.seek(0, 2)

    def __leaveElement(self):
        assert len(self.__shouldOutputStack) > 1
        self.__shouldOutputStack.pop()
        self.__currentNode = self.__currentNode.parent

    # XXX REFACTOR
    def _enterImg(self, tag, attributes):
        if True not in map(lambda attr: attr[0] not in ("src", "alt", "title"),
                           attributes):
            attributes = dict(attributes)
            parameters = {"url": attributes["src"]}
            if "alt" in attributes:
                parameters["alternateText"] = attributes["alt"]
            if "title" in attributes:
                parameters["title"] = attributes["title"]
            image = Image(**parameters)
            self.__currentNode.addChild(image)
            return image
        else:
            return None
    _enterImg.isBlock = False

    __numericEntityRegexp = re.compile("&#(x[0-9A-F]{2}|[0-9]{2,3});")

    def __substituteNumericEntity(self, match):
        return self.__translateNumericEntity(match.group(1))
    
    def __translateNumericEntity(self, ref):
        if ref[0] == "x":
            value = int(ref[1:], 16)
        else:
            value = int(ref)
        if self.__shouldDecodeNumericEntity(value):
            return chr(value)
        else:
            return "&#%s;" % (ref,)

    def __shouldDecodeNumericEntity(self, characterCode):
        return 32 <= characterCode <= 126

    def _enterA(self, tag, attributes):
        if all([ attr[0] in ("href", "title") for attr in attributes ]):
            attributes = dict(attributes)
            # XXX REFACTOR This indentation/wrapping is ugly and looks
            # unnecessary.  Should think about reducing name lengths.
            href = self.__numericEntityRegexp.sub(
                self.__substituteNumericEntity, attributes["href"])
            anchor = Anchor(href, title=attributes.get("title", None))
            self.__currentNode.addChild(anchor)
            return anchor
        else:
            return None
    _enterA.isBlock = False

    # XXX TEST <h*> with attributes.
    def _enterHeading(self, tag, attributes):
        level = int(tag[1:])
        heading = Heading(level)
        self.__currentNode.addChild(heading)
        return heading
    _enterHeading.isBlock = True

    def __shouldOutput(self):
        return self.__shouldOutputStack[-1]

    def handle_data(self, data):
        if self.__shouldOutput():
            log.debug("output %r" % (data,))
            self.__currentNode.addChild(Text(data))

    def handle_entityref(self, name):
        log.debug("entity=%r" % (name,))
        if not self.__unsupportedElementDepth:
            if name in self.__translatedEntities:
                self.handle_data(self.__translatedEntities[name])
            else:
                self.handle_data("&%s;" % (name,))

    def handle_charref(self, ref):
        if not self.__unsupportedElementDepth:
            self.handle_data(self.__translateNumericEntity(ref))

    # XXX some day we should probably change this interface to write
    # to a file, or to a callable
    def getOutput(self):
        assert isinstance(self.__currentNode, Document), `self.__currentNode`
        log.debug(self.__renderTreeForDebug(self.__currentNode))
        box = MarkdownTransformer().transform(self.__currentNode)
        log.debug(self.__renderTreeForDebug(box))
        result = StringIO()
        box.render(result.write)
        return result.getvalue()

    # XXX OPTIMIZE Could short-circuit this code when debug is off, as
    # an alternative to not calling it (log.debug("%s" %
    # (__renderTreeForDebug(),))).
    def __renderTreeForDebug(self, node):
        result = StringIO()
        result.write("(%s" % (node.__class__.__name__,))
        if hasattr(node, "children"):
            for child in node.children:
                result.write(" ")
                result.write(self.__renderTreeForDebug(child))
        result.write(")")
        return result.getvalue()

    __recognizedTags = {"p": Paragraph,
                        "blockquote": BlockQuote,
                        "ol": OrderedList,
                        "ul": UnorderedList,
                        "li": ListItem,
                        "code": Code,
                        "em": Emphasized,
                        "pre": Preformatted,
                        "br": LineBreak,
                        "img": _enterImg,
                        "hr": HorizontalRule,
                        "a": _enterA,
                        "strong": Strong}
    for level in range(1, 10):
        __recognizedTags["h%d" % (level,)] = _enterHeading


def html2markdown(html):
    return html2markdown_file(StringIO(html))

def html2markdown_file(inputFile):
    translator = MarkdownTranslator()
    for line in inputFile:
        translator.feed(line)
    translator.close()
    return 0, translator.getOutput()

if __name__ == "__main__": #pragma: no cover
    logging.basicConfig()
    if len(sys.argv) > 1:
        inputFile = open(sys.argv[1], "r")
    else:
        inputFile = sys.stdin
    status, output = html2markdown_file(inputFile)
    if status == 0:
        sys.stdout.write(output)
    sys.exit(status)
