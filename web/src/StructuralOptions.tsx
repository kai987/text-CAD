import { useEffect, useId, useState } from 'react';
import { asset } from './data';
import { useLanguage } from './LanguageContext';
import { useStructuralDesign } from './StructuralDesignContext';
import { createAsyncResourceCache } from './async-resource-cache';
import {
  cityNames, designCities, isDesignCity, isStructuralSystem, structuralCopy, structuralPaths,
  structuralSystems, systemNames,
} from './structural-design';
import type { RegulatoryProfiles, StructuralVariants } from './structural-design';

const profiles = createAsyncResourceCache<RegulatoryProfiles>(async path => {
  const response = await fetch(asset(path));
  if (!response.ok) throw new Error('Regulatory profiles unavailable.');
  return response.json();
});
const variants = createAsyncResourceCache<StructuralVariants>(async path => {
  const response = await fetch(asset(path));
  if (!response.ok) throw new Error('Structural variant metadata unavailable.');
  return response.json();
});
const profilePath = 'output/review/regulatory_profiles_R07.json';
const variantPath = 'output/review/structural_variants_R07.json';

export function StructuralDownloads() {
  const { locale } = useLanguage();
  const { design } = useStructuralDesign();
  const paths = structuralPaths(design);
  return <div className="structural-downloads">
    <a href={asset(paths.glb)} download>{structuralCopy.downloadGlb[locale]}</a>
    <a href={asset(paths.step)} download>{structuralCopy.downloadStep[locale]}</a>
    <a href={asset(paths.case)} download>{structuralCopy.downloadCase[locale]}</a>
  </div>;
}

export default function StructuralOptions({ compact = false, showSelectors = true, showSummary = false }: { compact?: boolean; showSelectors?: boolean; showSummary?: boolean }) {
  const { locale } = useLanguage();
  const { design, setDesign } = useStructuralDesign();
  const controlId = useId();
  const [data, setData] = useState(() => profiles.getCached(profilePath));
  const [schemes, setSchemes] = useState(() => variants.getCached(variantPath));
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let alive = true;
    setFailed(false);
    void Promise.all([profiles.load(profilePath), variants.load(variantPath)]).then(([next, options]) => {
      if (alive) { setData(next); setSchemes(options); }
    }).catch(() => { if (alive) setFailed(true); });
    return () => { alive = false; };
  }, [attempt]);
  const profile = data?.profiles.find(item => item.id === design.city);
  const summary = schemes?.variants[design.system]?.coordination.summary;
  const nationalRequirements = data?.national_requirements.filter(item => item.id !== 'current_timber_rules' || design.system === 'W') ?? [];
  const referencedIds = new Set([
    ...nationalRequirements.flatMap(item => item.source_ids ?? []),
    ...profile?.review_items.flatMap(item => item.source_ids ?? []) ?? [],
    ...Object.values(profile?.environmental_parameters ?? {}).flatMap(item => item.source_ids ?? []),
  ]);
  const sources = data?.sources.filter(source => referencedIds.has(source.id)) ?? [];
  return <section className={compact ? 'structural-options compact' : 'structural-options'} aria-label={structuralCopy.title[locale]}>
    {!compact ? <h2>{structuralCopy.title[locale]} <span className="structural-revision">R13</span></h2> : null}
    {showSelectors ? <div className="structural-selectors">
      <div><label htmlFor={`${controlId}-city`}>{structuralCopy.city[locale]}</label>
        <select id={`${controlId}-city`} value={design.city} onChange={event => {
          if (isDesignCity(event.target.value)) setDesign({ ...design, city: event.target.value });
        }}>{designCities.map(city => <option key={city} value={city}>{cityNames[city][locale]}</option>)}</select>
      </div>
      <div><label htmlFor={`${controlId}-system`}>{structuralCopy.system[locale]}</label>
        <select id={`${controlId}-system`} value={design.system} onChange={event => {
          if (isStructuralSystem(event.target.value)) setDesign({ ...design, system: event.target.value });
        }}>{structuralSystems.map(system => <option key={system} value={system}>{systemNames[system][locale]}</option>)}</select>
      </div>
    </div> : <p className="structural-chosen">{cityNames[design.city][locale]} · {systemNames[design.system][locale]}</p>}
    {compact && showSummary && summary ? <p className="structural-explanation">{summary[locale]}</p> : null}
    {!compact ? <>
      <p className="structural-status">{structuralCopy.status[locale]}</p>
      <p className="structural-explanation">{structuralCopy.introduction[locale]}</p>
      <StructuralDownloads />
      <details className="structural-details">
        <summary>{structuralCopy.details[locale]}</summary>
        {!profile ? <p role={failed ? 'alert' : 'status'}>{failed ? structuralCopy.profileError[locale] : structuralCopy.profileLoading[locale]}</p> : <>
          <p>{profile.authority[locale]}</p>
          <p>{profile.jurisdiction_scope[locale]}</p>
          <h3>{structuralCopy.national[locale]}</h3>
          <ul>{nationalRequirements.map(item => <li key={item.id}>{item.text[locale]}</li>)}</ul>
          <h3>{structuralCopy.referenceValues[locale]}</h3>
          <dl className="structural-reference-values">
            {Object.entries(profile.environmental_parameters).map(([key, value]) => <div key={key}>
              <dt>{key in structuralCopy ? structuralCopy[key as keyof typeof structuralCopy][locale] : key}</dt>
              <dd>{value.value === null ? structuralCopy.pending[locale] : `${value.value}${value.unit ? ` ${value.unit}` : ''}`}<span>{value.scope[locale]}</span></dd>
            </div>)}
          </dl>
          <ul>{profile.review_items.map(item => <li key={item.id}>{item.text[locale]}</li>)}</ul>
          <h3>{structuralCopy.required[locale]}</h3>
          <p>{structuralCopy.commonInputs[locale]}</p>
          {profile.pending_site_inputs.some(input => typeof input !== 'string') ? <ul>{profile.pending_site_inputs.map(input => typeof input === 'string' ? null : <li key={input.id}>{input.text[locale]}</li>)}</ul> : null}
          <h3>{structuralCopy.references[locale]}</h3>
          <ul className="structural-source-links">{sources.map(source => <li key={source.id}>
            <a href={source.url} target="_blank" rel="noreferrer">{typeof source.title === 'string' ? source.title : source.title[locale]}</a>
          </li>)}</ul>
          <p>{structuralCopy.referencesChecked[locale]}: {data?.checked_at.slice(0, 10)}</p>
        </>}
        {failed ? <button type="button" className="outline-button" onClick={() => setAttempt(value => value + 1)}>{structuralCopy.retry[locale]}</button> : null}
        <h3>{structuralCopy.coordination[locale]}</h3>
        <p>{summary?.[locale] ?? structuralCopy.exterior[locale]}</p>
        {summary ? <p>{structuralCopy.exterior[locale]}</p> : null}
      </details>
    </> : null}
  </section>;
}
