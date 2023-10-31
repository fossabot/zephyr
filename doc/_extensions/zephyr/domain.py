"""
Zephyr Extension
################

Copyright (c) 2023 The Linux Foundation
SPDX-License-Identifier: Apache-2.0

Introduction
============

This extension adds a new ``zephyr`` domain for handling the documentation of various entities
specific to the Zephyr RTOS project (ex. code samples).

Directives
----------

- ``zephyr:code-sample::`` - Defines a code sample.
  The directive takes an ID as the main argument, and accepts ``:name:`` (human-readable short name
  of the sample) and ``:relevant-api:`` (a space separated list of Doxygen group(s) for APIs the
  code sample is a good showcase of) as options.
  The content of the directive is used as the description of the code sample.

  Example:

  ```
  .. zephyr:code-sample:: blinky
     :name: Blinky
     :relevant-api: gpio_interface

     Blink an LED forever using the GPIO API.
 ```

Roles
-----

- ``:zephyr:code-sample:`` - References a code sample.
  The role takes the ID of the code sample as the argument. The role renders as a link to the code
  sample, and the link text is the name of the code sample (or a custom text if an explicit name is
  provided).

  Example:

  ```
  Check out :zephyr:code-sample:`sample-foo` for an example of how to use the foo API. You may
  also be interested in :zephyr:code-sample:`this one <sample-bar>`.
  ```

"""
from os import path
from typing import Any, Dict, Iterator, List, Tuple

from breathe.directives.content_block import DoxygenGroupDirective
from docutils import nodes
from docutils.nodes import Node, system_message
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.nodes import NodeMatcher, make_refnode
from zephyr.gh_utils import gh_link_get_url

import json

__version__ = "0.1.0"

logger = logging.getLogger(__name__)


class CodeSampleNode(nodes.Element):
    pass


class RelatedCodeSamplesNode(nodes.Element):
    pass


class CodeSampleListingNode(nodes.Element):
    pass


class ConvertCodeSampleNode(SphinxTransform):
    default_priority = 100

    def apply(self):
        matcher = NodeMatcher(CodeSampleNode)
        for node in self.document.traverse(matcher):
            self.convert_node(node)

    def convert_node(self, node):
        """
        Transforms a `CodeSampleNode` into a `nodes.section` named after the code sample name.

        Moves all sibling nodes that are after the `CodeSampleNode` in the documement under this new
        section.
        """
        parent = node.parent
        siblings_to_move = []
        if parent is not None:
            index = parent.index(node)
            siblings_to_move = parent.children[index + 1 :]

            # Create a new section
            new_section = nodes.section(ids=[node["id"]])
            new_section += nodes.title(text=node["name"])

            # Move the sibling nodes under the new section
            new_section.extend(siblings_to_move)

            # Replace the custom node with the new section
            node.replace_self(new_section)

            # Remove the moved siblings from their original parent
            for sibling in siblings_to_move:
                parent.remove(sibling)

            # Set sample description as the meta description of the document for improved SEO
            meta_description = nodes.meta()
            meta_description["name"] = "description"
            meta_description["content"] = node.children[0].astext()
            node.document += meta_description

            # Similarly, add a node with JSON-LD markup (only renders in HTML output) describing
            # the code sample.
            json_ld = nodes.raw(
                "",
                f"""<script type="application/ld+json">
                {json.dumps({
                    "@context": "http://schema.org",
                    "@type": "SoftwareSourceCode",
                    "name": node['name'],
                    "description": node.children[0].astext(),
                    "codeSampleType": "full",
                    "codeRepository": gh_link_get_url(self.app, self.env.docname)
                })}
                </script>""",
                format="html",
            )
            node.document += json_ld


class ProcessCodeSampleListingNode(SphinxPostTransform):
    default_priority = 4

    def run(self, **kwargs: Any) -> None:
        matcher = NodeMatcher(CodeSampleListingNode)
        for node in self.document.traverse(matcher):
            print("Post transform of code sample listing: ", node)

            # Get all categories
            categories = self.env.domaindata["zephyr"]["code-samples-categories"]
            # Print the names of all categories
            print("Categories: ", categories)

            node_list = []
            # create a section for each category
            for category_name, category_description in categories.items():
                category_section = nodes.section(ids=[f"{category_name}-sample-category-x"])
                category_section += nodes.title(text=category_name)
                category_section += nodes.paragraph(text="BIDON FOR NOW")

                toctree = addnodes.toctree()
                toctree["maxdepth"] = 1
                toctree["hidden"] = False
                toctree["glob"] = False
                toctree["parent"] = self.env.docname
                toctree["entries"] = []
                toctree["includefiles"] = []
                toctree["entries"].append(("TESTTOC", "snippets/xen_dom0/README"))

                category_section += toctree

                category_section += nodes.paragraph(text="BIDON FOR NOW222")


                node_list.append(category_section)

            node.replace_self(node_list)


def create_code_sample_definition_list(code_samples):
    """
    Creates a definition list (`nodes.definition_list`) of code samples from a list of code sample.

    The definition list is sorted alphabetically by the name of the code sample.
    The "term" is set to the name of the code sample, and the "definition" is set to its
    description.
    """

    dl = nodes.definition_list()

    for code_sample in sorted(code_samples, key=lambda x: x["name"].casefold()):
        term = nodes.term()

        sample_xref = addnodes.pending_xref(
            "",
            refdomain="zephyr",
            reftype="code-sample",
            reftarget=code_sample["id"],
            refwarn=True,
        )
        sample_xref += nodes.inline(text=code_sample["name"])
        term += sample_xref
        definition = nodes.definition()
        definition += nodes.paragraph(text=code_sample["description"].astext())
        sample_dli = nodes.definition_list_item()
        sample_dli += term
        sample_dli += definition
        dl += sample_dli

    return dl


class ProcessRelatedCodeSamplesNode(SphinxPostTransform):
    default_priority = 5  # before ReferencesResolver

    def run(self, **kwargs: Any) -> None:
        matcher = NodeMatcher(RelatedCodeSamplesNode)
        for node in self.document.traverse(matcher):
            id = node["id"]  # the ID of the node is the name of the doxygen group for which we
            # want to list related code samples

            code_samples = self.env.domaindata["zephyr"]["code-samples"].values()
            # Filter out code samples that don't reference this doxygen group
            code_samples = [
                code_sample for code_sample in code_samples if id in code_sample["relevant-api"]
            ]

            if len(code_samples) > 0:
                admonition = nodes.admonition()
                admonition += nodes.title(text="Related code samples")
                admonition["classes"].append("related-code-samples")
                admonition["classes"].append("dropdown")  # used by sphinx-togglebutton extension
                admonition["classes"].append("toggle-shown")  # show the content by default

                samples_dl = create_code_sample_definition_list(code_samples)
                admonition += samples_dl

                # replace node with the newly created admonition
                node.replace_self(admonition)
            else:
                # remove node if there are no code samples
                node.replace_self([])


class CodeSampleDirective(Directive):
    """
    A directive for creating a code sample node in the Zephyr documentation.
    """

    required_arguments = 1  # ID
    optional_arguments = 0
    option_spec = {"name": directives.unchanged, "relevant-api": directives.unchanged}
    has_content = True

    def run(self):
        code_sample_id = self.arguments[0]
        env = self.state.document.settings.env
        code_samples = env.domaindata["zephyr"]["code-samples"]

        # implicitly mark the document as orphan, as its appearance in the table of contents is
        # going to be controlled by the `code-sample-listing` directive.
        env.metadata[env.docname]["orphan"] = True

        if code_sample_id in code_samples:
            logger.warning(
                f"Code sample {code_sample_id} already exists. "
                f"Other instance in {code_samples[code_sample_id]['docname']}",
                location=(env.docname, self.lineno),
            )

        name = self.options.get("name", code_sample_id)
        relevant_api_list = self.options.get("relevant-api", "").split()

        # Create a node for description and populate it with parsed content
        description_node = nodes.container(ids=[f"{code_sample_id}-description"])
        self.state.nested_parse(self.content, self.content_offset, description_node)

        code_sample = {
            "id": code_sample_id,
            "name": name,
            "description": description_node,
            "relevant-api": relevant_api_list,
            "docname": env.docname,
        }

        domain = env.get_domain("zephyr")
        domain.add_code_sample(code_sample)

        # Create an instance of the custom node
        code_sample_node = CodeSampleNode()
        code_sample_node["id"] = code_sample_id
        code_sample_node["name"] = name
        code_sample_node += description_node

        return [code_sample_node]


class CodeSampleCategoryDirective(SphinxDirective):
    required_arguments = 1  # Category name
    optional_arguments = 0
    option_spec = {}
    has_content = True  # Category description
    final_argument_whitespace = True

    def run(self):
        env = self.state.document.settings.env
        name = self.arguments[0]

        # Create a section named after the category name
        category_node = nodes.section(ids=[f"{name}-sample-category"])
        category_node += nodes.title(text=name)

        # Create a node for description and populate it with parsed content
        description_node = nodes.container(ids=[f"{name}-description"])
        self.state.nested_parse(self.content, self.content_offset, description_node)

        category_node += description_node

        # Add the category to the domain
        domain = env.get_domain("zephyr")
        domain.add_code_sample_category(name, description_node)

        return [category_node]


class CodeSampleListingDirective(SphinxDirective):
    """
    A directive that automatically shows a listing of all code samples found in the subdirectories
    of the current document.

    The toc is hidden, and only exists for the purpose of generating an alphabetically sorted
    list of code samples in the sidebar.

    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    option_spec = {}

    def run(self):
        print("CodeSampleListingDirective")
        env = self.state.document.settings.env
        code_samples = env.domaindata["zephyr"]["code-samples"]

        toctree = addnodes.toctree()
        toctree["maxdepth"] = 1
        toctree["hidden"] = True
        toctree["glob"] = False
        toctree["parent"] = env.docname
        toctree["entries"] = []
        toctree["includefiles"] = []
        self.env.note_reread()

        dl = create_code_sample_definition_list(
            [
                code_sample
                for code_sample in code_samples.values()
                if path.dirname(code_sample["docname"]).startswith(path.dirname(env.docname))
            ]
        )

        for code_sample in sorted(code_samples.values(), key=lambda x: x["name"].casefold()):
            # if the code sample is in the hierarchy of the document, add it to the toc
            if path.dirname(code_sample["docname"]).startswith(path.dirname(env.docname)):
                toctree["entries"].append((code_sample["name"], code_sample["docname"]))
                toctree["includefiles"].append(code_sample["docname"])

        return [dl, toctree, CodeSampleListingNode()]


class ZephyrDomain(Domain):
    """Zephyr domain"""

    name = "zephyr"
    label = "Zephyr Project"

    roles = {
        "code-sample": XRefRole(innernodeclass=nodes.inline, warn_dangling=True),
    }

    directives = {
        "code-sample": CodeSampleDirective,
        "code-sample-listing": CodeSampleListingDirective,
        "code-sample-category": CodeSampleCategoryDirective,
    }

    object_types: Dict[str, ObjType] = {
        "code-sample": ObjType("code sample", "code-sample"),
    }

    initial_data: Dict[str, Any] = {
                                        "code-samples": {},
                                        "code-samples-categories": {}
                                    }

    def clear_doc(self, docname: str) -> None:
        self.data["code-samples"] = {
            sample_id: sample_data
            for sample_id, sample_data in self.data["code-samples"].items()
            if sample_data["docname"] != docname
        }
        # TODO handle removal of categories

    def merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None:
        self.data["code-samples"].update(otherdata["code-samples"])
        self.data["code-samples-categories"].update(otherdata["code-samples-categories"])

    def get_objects(self):
        for _, code_sample in self.data["code-samples"].items():
            yield (
                code_sample["name"],
                code_sample["name"],
                "code sample",
                code_sample["docname"],
                code_sample["id"],
                1,
            )

    # used by Sphinx Immaterial theme
    def get_object_synopses(self) -> Iterator[Tuple[Tuple[str, str], str]]:
        for _, code_sample in self.data["code-samples"].items():
            yield (
                (code_sample["docname"], code_sample["id"]),
                code_sample["description"].astext(),
            )

    def resolve_xref(self, env, fromdocname, builder, type, target, node, contnode):
        if type == "code-sample":
            code_sample_info = self.data["code-samples"].get(target)
            if code_sample_info:
                if not node.get("refexplicit"):
                    contnode = [nodes.Text(code_sample_info["name"])]

                return make_refnode(
                    builder,
                    fromdocname,
                    code_sample_info["docname"],
                    code_sample_info["id"],
                    contnode,
                    code_sample_info["description"].astext(),
                )

    def add_code_sample(self, code_sample):
        self.data["code-samples"][code_sample["id"]] = code_sample

    def add_code_sample_category(self, name, description):
        self.data["code-samples-categories"][name] = description


class CustomDoxygenGroupDirective(DoxygenGroupDirective):
    """Monkey patch for Breathe's DoxygenGroupDirective."""

    def run(self) -> List[Node]:
        nodes = super().run()
        return [RelatedCodeSamplesNode(id=self.arguments[0]), *nodes]


def setup(app):
    app.add_domain(ZephyrDomain)

    app.add_transform(ConvertCodeSampleNode)
    app.add_post_transform(ProcessCodeSampleListingNode)
    app.add_post_transform(ProcessRelatedCodeSamplesNode)

    # monkey-patching of Breathe's DoxygenGroupDirective
    app.add_directive("doxygengroup", CustomDoxygenGroupDirective, override=True)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
