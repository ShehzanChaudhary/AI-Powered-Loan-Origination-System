from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

_env = Environment(loader=FileSystemLoader(Path(__file__).parent))

def render_prompt(template_name: str, **kwargs) -> Template:
    """Renders a .jinja2 prompt template with the given variables."""
    template = _env.get_template(template_name)
    return template.render(**kwargs)