from __future__ import annotations

import argparse
import os
import shutil
import sys
import typing as t
from dataclasses import dataclass
from pathlib import Path
from random import randint

from faker import Faker
from jinja2 import Environment, PackageLoader


@dataclass
class Repository:
    """A fake repository"""

    basedir: str
    name: str
    owner: str

    def generate_documentation_files(self):
        """Generates markdown documenation files according to the guidelines."""


@dataclass
class MultirepoFactory:
    """Responsible for creating the multi-repo setup."""

    repositories: t.List[Repository]

    def generate_multirepo_setup(self):
        """Generate multirepo directories with initial git commits."""

    def add_changes_and_bump_versions(self):
        """Randomly add changes to repository files and bump version (minor,major or patch)."""


#: This are the allowed content types
ContentType = t.Union[
    t.Literal["learn"],
    t.Literal["guide"],
    t.Literal["reference"],
    t.Literal["tutorial"],
]


@dataclass
class Document:
    """A markdown document which belongs to some content-type."""

    name: str
    template_name: str
    template_vars: dict
    relative_path: str = ""
    basepath: t.Optional[Path] = None
    jinja = Environment(loader=PackageLoader("mockrepos"))

    def create(self, write: bool = False):
        """Create document based on content-type"""
        template = self.jinja.get_template(self.template_name)
        data = template.render(**self.template_vars)

        # write
        if write and self.basepath:
            filename = "{}.md".format(self.name)
            if self.relative_path:
                dir_path = self.basepath / self.relative_path
            else:
                dir_path = self.basepath
            dir_path.mkdir(parents=True, exist_ok=True)
            Path(dir_path / filename).write_text(data)
        return data


@dataclass
class ContentFactory:
    """Creates a Document or Documents list with content-type templates."""

    basepath: t.Optional[Path] = None
    template_name = "content_templates"
    templates = ("guide_page", "tutorial_page", "tutorial_main", "learn_page")
    content = ("learn", "guide", "tutorial")
    faker = Faker()

    def create_guide(
        self,
        title: t.Optional[str] = None,
        repository: t.Optional[str] = None,
        persona: t.Optional[str] = None,
    ) -> Document:
        """Creates a guide"""
        verbs = ["do", "create", "generate", "bind", "delete", "update"]

        def gen_paragraph():
            return " ".join((self.faker.paragraph()) for _ in range(3))

        def gen_imperative():
            return "{} {}".format(
                self.faker.word(ext_word_list=verbs),
                self.faker.sentence(nb_words=3).lower(),
            )

        # optional kwargs
        title = title or "How to {}".format(gen_imperative()[:-1])
        repository = repository or "default"
        persona = persona or self.faker.word(ext_word_list=["admin", "dev", "norm"])

        # guide generation
        n_steps = randint(2, 4)
        steps = [gen_imperative() for _ in range(n_steps)]

        template_vars = {
            "tags": ["guide", persona],
            "created": "0.1.0",
            "updated": [],
            "title": title,
            "overview": gen_paragraph(),
            "steps": steps,
            "sections": [
                ("{} - {}".format(i + 1, step), gen_paragraph())
                for i, step in enumerate(steps)
            ],
        }
        relative_path = "{}/guides".format(persona)
        return Document(
            title,
            "guide_page.md.j2",
            template_vars,
            relative_path=relative_path,
            basepath=self.basepath,
        )

    def create_learn(
        self,
        title: t.Optional[str] = None,
        repository: t.Optional[str] = None,
        persona: t.Optional[str] = None,
    ) -> Document:
        """Creates a learn"""
        subject = ["database", "model", "content", "artifact", "repository"]
        subject_complement = ["configuration", "deployment", "ecossystem", "setup"]
        adjective = [
            "resilient",
            "complex",
            "flexible",
            "autonomous",
            "modular",
            "scalable",
        ]
        introductory = ["On", "About", "In perspective:", "Understanding"]

        def gen_paragraphs():
            return " ".join((self.faker.paragraph()) for _ in range(3))

        def gen_title():
            return " ".join(
                [
                    self.faker.word(ext_word_list=introductory),
                    self.faker.word(ext_word_list=adjective),
                    self.faker.word(ext_word_list=subject).title(),
                    self.faker.word(ext_word_list=subject_complement),
                ]
            )

        def gen_section():
            return (
                self.faker.sentence()[:-1],
                "\n\n".join(
                    self.faker.texts(
                        nb_texts=randint(3, 5), max_nb_chars=randint(200, 400)
                    )
                ),
            )

        title = title or gen_title()
        persona = persona or self.faker.word(ext_word_list=["admin", "dev", "norm"])
        repository = repository or "default"

        template_vars = {
            "tags": ["learn", persona],
            "created": "0.1.0",
            "updated": [],
            "title": title,
            "overview": gen_paragraphs(),
            "sections": [gen_section() for _ in range(randint(2, 4))],
        }
        relative_path = "{}/learn".format(persona)
        return Document(
            title,
            "learn_page.md.j2",
            template_vars,
            relative_path=relative_path,
            basepath=self.basepath,
        )

    def create_tutorial(
        self,
        title: t.Optional[str] = None,
        repository: t.Optional[str] = None,
        persona: t.Optional[str] = None,
    ) -> t.List[Document]:
        """Creates a tutorial"""
        documents = []
        subject = [
            "the database",
            "the model",
            "the content",
            "the artifact",
            "the repository",
        ]
        verb = [
            "configuring",
            "deploying",
            "setting",
            "organizing",
            "doing",
            "handling",
        ]
        adjective = [
            "infrastructure",
            "internals",
            "contexts",
            "dependencie",
            "relationships",
            "signals",
        ]
        topics = ["Content Management", "Development", "System Administration"]

        def gen_paragraphs(n: t.Optional[int] = None):
            n = n or 3
            return " ".join((self.faker.paragraph()) for _ in range(n))

        def gen_title():
            return "Getting started with {}".format(
                self.faker.word(ext_word_list=topics)
            )

        def gen_section_title():
            return " ".join(
                [
                    self.faker.word(ext_word_list=verb).title(),
                    self.faker.word(ext_word_list=subject),
                    self.faker.word(ext_word_list=adjective),
                ]
            )

        def gen_section():
            return (
                self.faker.sentence()[:-1],
                "\n\n".join(
                    self.faker.texts(
                        nb_texts=randint(3, 5), max_nb_chars=randint(200, 400)
                    )
                ),
            )

        persona = persona or self.faker.word(ext_word_list=["admin", "dev", "norm"])
        title = title or "Getting started as {}".format(persona)
        repository = repository or "default"
        tags = ["tutorial", persona]

        # generate main page
        main_title = "00 - {}".format(title)
        template_vars = {
            "tags": tags,
            "created": "0.1.0",
            "updated": [],
            "title": main_title,
            "overview": gen_paragraphs(5),
            "sections": [gen_section() for _ in range(randint(2, 4))],
        }
        relative_path = "{}/tutorials/{}".format(persona, title)
        documents.append(
            Document(
                main_title,
                "tutorial_main.md.j2",
                template_vars,
                relative_path=relative_path,
                basepath=self.basepath,
            )
        )

        # generate each page of the tutorial
        for i in range(randint(2, 4)):
            section_title = "0{} - {}".format(i + 1, gen_section_title())
            template_vars = {
                "tags": ["tutorial", persona],
                "created": "0.1.0",
                "updated": [],
                "title": section_title,
                "overview": gen_paragraphs(),
                "sections": [gen_section() for _ in range(randint(2, 4))],
            }
            documents.append(
                Document(
                    section_title,
                    "tutorial_main.md.j2",
                    template_vars,
                    relative_path=relative_path,
                    basepath=self.basepath,
                )
            )

        return documents


@dataclass
class DocumentationFactory:
    """Generates Diataxis-based documentation for Pulp"""

    basepath: Path

    def create_documentation(self) -> t.List[Document]:
        """Create Documents based for all repositories."""
        documents: t.List[Document] = []

        # create content for one repo
        content_factory = ContentFactory(self.basepath)
        for persona in ("developer", "content-manager", "sys-admin"):
            [
                content_factory.create_guide(persona=persona).create(write=True)
                for _ in range(randint(1, 5))
            ]
            [
                content_factory.create_learn(persona=persona).create(write=True)
                for _ in range(randint(1, 5))
            ]
            [
                tuto.create(write=True)
                for tuto in content_factory.create_tutorial(persona=persona)
            ]

        return documents


def main():
    # parse args
    parser = argparse.ArgumentParser(
        "docs_generator",
        description="Genreate a doc structure populated with fake data",
    )
    parser.add_argument(
        "basepath", help="The basepath where the documentation folder will be created"
    )
    args = parser.parse_args()
    basepath = Path() / args.basepath

    # ensure won't unintended override a direcotory
    if basepath.exists():
        overwrite = input(
            f"{basepath} exists, do you wanna override? (N/y): "
        ).lower() in ("y", "yes")
        if overwrite:
            print(f"Cleaned: {basepath.absolute()}.")
            shutil.rmtree(basepath)
        else:
            print("Did not overwritte. Nothing to do.")
            return 0

    # create documentation
    basepath.mkdir()
    documentation_factory = DocumentationFactory(basepath / "docs")
    documentation_factory.create_documentation()


if __name__ == "__main__":
    sys.exit(main())
