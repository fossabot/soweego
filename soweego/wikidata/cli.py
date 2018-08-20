import click
from soweego.wikidata import query_on_values, sample_additional_info

CLI_COMMANDS = {
    'query_on_values': query_on_values.main,
    'get_sitelinks_for_sample': sample_additional_info.get_sitelinks_for_sample,
    'get_links_for_sample': sample_additional_info.get_links_for_sample,
    'get_birth_death_dates_for_sample':
        sample_additional_info.get_birth_death_dates_for_sample,
    'get_url_formatters_for_properties':
        sample_additional_info.get_url_formatters_for_properties
}


@click.group(name='wikidata', commands=CLI_COMMANDS)
@click.pass_context
def cli(ctx):
    """Read/write operations on the knowledge base"""
    pass
