import { css } from "lit";

/**
 * The band across the top: the chrome that carries what is true of the whole
 * system the UI is about.
 *
 * Its colours are the look rules' and are the same in every rails49 UI, so it
 * asks `look.css` for them rather than naming one. It is the height of a rail
 * button at least, which is what keeps the two pieces of chrome reading as one
 * edge on a phone.
 */
export const bandStyles = css`
  :host {
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-sizing: border-box;
    min-height: var(--rail-button);
    padding: 0 0.75rem;
    background: var(--band);
    color: var(--band-ink);
  }

  .name {
    font-weight: 600;
    letter-spacing: 0.02em;
  }
`;
