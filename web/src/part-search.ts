import type { ModelLayout, GroupId, ModelPartId } from './model-state.ts';

export function filterPartTree(layout: ModelLayout, query: string, groupLabel: (id: GroupId) => string, partLabel: (id: ModelPartId) => string) {
  const normalize = (value: string) => value.normalize('NFKC').toLocaleLowerCase().trim();
  const needle = normalize(query);
  return layout.groups.flatMap(group => {
    const children = layout.parts.filter(part => part.group === group.id);
    const groupMatches = normalize(`${groupLabel(group.id)} ${group.id}`).includes(needle);
    const matches = !needle || groupMatches ? children : children.filter(part => normalize(`${groupLabel(group.id)} ${partLabel(part.id)} ${part.id}`).includes(needle));
    return !needle || groupMatches || matches.length ? [{ group, children: matches }] : [];
  });
}
