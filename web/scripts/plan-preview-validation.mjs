import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const contained = (bounds, [x, y, width, height]) =>
  bounds[0] >= x && bounds[1] >= y && bounds[2] <= x + width && bounds[3] <= y + height;

export function validatePlanMetadata(metadata, pdfBytes, svgByFloor,
  { floors = [1, 2], dimensions = ['7280', '7280'] } = {}) {
  if (metadata.version !== 1 || metadata.source.sha256 !== sha(pdfBytes)) {
    throw new Error('Vector plans are stale: regenerate SVG from the current approved PDF.');
  }
  if (metadata.source.pages !== floors.length || metadata.floors.length !== floors.length ||
      metadata.floors.some((floor, index) => floor.floor !== floors[index]) || !metadata.generator.textAsPath) {
    throw new Error(`Expected ${floors.length} outlined floor-plan SVGs in floor order.`);
  }
  for (const floor of metadata.floors) {
    const svg = svgByFloor.get(floor.floor);
    if (!svg || sha(svg) !== floor.sha256 || svg.length !== floor.bytes) {
      throw new Error(`Vector floor ${floor.floor} differs from its recorded PDF conversion.`);
    }
    const text = svg.toString('utf8');
    if (!text.startsWith('<svg ') || !/<path\b/.test(text) || !/<use\b/.test(text) ||
        /<(?:text|image|script|foreignObject)\b/i.test(text) || /\son\w+\s*=/i.test(text) ||
        /(?:href|xlink:href)="(?!#)/i.test(text)) {
      throw new Error(`Vector floor ${floor.floor} must contain only local vector geometry and outlined text.`);
    }
    const [x, y, width, height] = floor.planViewBox;
    if (![x, y, width, height].every(Number.isFinite) || width <= 0 || height <= 0 ||
        !contained([x, y, x + width, y + height], floor.fullViewBox)) {
      throw new Error(`Vector floor ${floor.floor} has an invalid plan crop.`);
    }
    if (floor.annotations.some(annotation => !contained(annotation.bounds, floor.planViewBox))) {
      throw new Error(`Vector floor ${floor.floor} crop clips a recorded annotation.`);
    }
    const missingDimension = [...new Set(dimensions)].some(dimension =>
      floor.annotations.filter(annotation => annotation.text === dimension).length <
      dimensions.filter(value => value === dimension).length);
    if (missingDimension ||
        floor.requiredLabels.some(label => !floor.annotations.some(annotation => annotation.text.includes(label)))) {
      throw new Error(`Vector floor ${floor.floor} crop omits a room or overall dimension.`);
    }
  }
  return metadata;
}

export async function validatePlanPreviews(root) {
  const metadata = JSON.parse(await readFile(resolve(root, 'web/src/plan-preview-metadata.json'), 'utf8'));
  const pdf = await readFile(resolve(root, metadata.source.path));
  const svgByFloor = new Map(await Promise.all(metadata.floors.map(async floor => [
    floor.floor, await readFile(resolve(root, floor.path)),
  ])));
  return validatePlanMetadata(metadata, pdf, svgByFloor);
}

export const apartmentPlanRequirements = { floors: [1], dimensions: ['7800', '8400'] };

export async function validateApartmentPreviews(root) {
  const metadata = JSON.parse(await readFile(resolve(root, 'output/review/apartment_2ldk_preview.json'), 'utf8'));
  const pdf = await readFile(resolve(root, metadata.source.path));
  const svgByFloor = new Map(await Promise.all(metadata.floors.map(async floor => [
    floor.floor, await readFile(resolve(root, floor.path)),
  ])));
  return validatePlanMetadata(metadata, pdf, svgByFloor, apartmentPlanRequirements);
}
