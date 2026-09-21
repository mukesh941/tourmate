/**
 * Canonical Image Utilities & Neutral Fallback Assets.
 * Prevents unauthorized or unrelated dummy travel photos from masquerading as entity media.
 */

export const NEUTRAL_PLACEHOLDER_IMAGE = 
  "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22800%22%20height%3D%22600%22%20viewBox%3D%220%200%20800%20600%22%20fill%3D%22none%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f1f5f9%22%2F%3E%3Ccircle%20cx%3D%22400%22%20cy%3D%22260%22%20r%3D%2248%22%20fill%3D%22%23cbd5e1%22%2F%3E%3Cpath%20d%3D%22M400%20228c-17.7%200-32%2014.3-32%2032%200%2028%2032%2056%2032%2056s32-28%2032-56c0-17.7-14.3-32-32-32zm0%2044c-6.6%200-12-5.4-12-12s5.4-12%2012-12%2012%205.4%2012%2012-5.4%2012-12%2012z%22%20fill%3D%22%2364748b%22%2F%3E%3Ctext%20x%3D%22400%22%20y%3D%22360%22%20fill%3D%22%23475569%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2220%22%20font-weight%3D%22600%22%20text-anchor%3D%22middle%22%3ETourMate%20Verified%20Destination%3C%2Ftext%3E%3Ctext%20x%3D%22400%22%20y%3D%22390%22%20fill%3D%22%2394a3b8%22%20font-family%3D%22system-ui%2C%20sans-serif%22%20font-size%3D%2214%22%20font-weight%3D%22400%22%20text-anchor%3D%22middle%22%3EAuthentic%20Travel%20%26%20Heritage%3C%2Ftext%3E%3C%2Fsvg%3E";

export const handleImageError = (e) => {
  e.target.onerror = null;
  e.target.src = NEUTRAL_PLACEHOLDER_IMAGE;
};
