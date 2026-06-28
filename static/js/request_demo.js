/* ════════════════════════════════════════════════
   DONNÉES PAYS — flag emoji + indicatif téléphonique
   ════════════════════════════════════════════════ */
const COUNTRIES = [
  { code: 'AF', name: 'Afghanistan',           flag: '🇦🇫', dial: '+93'   },
  { code: 'AL', name: 'Albania',               flag: '🇦🇱', dial: '+355'  },
  { code: 'DZ', name: 'Algeria',               flag: '🇩🇿', dial: '+213'  },
  { code: 'AD', name: 'Andorra',               flag: '🇦🇩', dial: '+376'  },
  { code: 'AO', name: 'Angola',                flag: '🇦🇴', dial: '+244'  },
  { code: 'AG', name: 'Antigua & Barbuda',     flag: '🇦🇬', dial: '+1'    },
  { code: 'AR', name: 'Argentina',             flag: '🇦🇷', dial: '+54'   },
  { code: 'AM', name: 'Armenia',               flag: '🇦🇲', dial: '+374'  },
  { code: 'AU', name: 'Australia',             flag: '🇦🇺', dial: '+61'   },
  { code: 'AT', name: 'Austria',               flag: '🇦🇹', dial: '+43'   },
  { code: 'AZ', name: 'Azerbaijan',            flag: '🇦🇿', dial: '+994'  },
  { code: 'BS', name: 'Bahamas',               flag: '🇧🇸', dial: '+1'    },
  { code: 'BH', name: 'Bahrain',               flag: '🇧🇭', dial: '+973'  },
  { code: 'BD', name: 'Bangladesh',            flag: '🇧🇩', dial: '+880'  },
  { code: 'BB', name: 'Barbados',              flag: '🇧🇧', dial: '+1'    },
  { code: 'BY', name: 'Belarus',               flag: '🇧🇾', dial: '+375'  },
  { code: 'BE', name: 'Belgium',               flag: '🇧🇪', dial: '+32'   },
  { code: 'BZ', name: 'Belize',                flag: '🇧🇿', dial: '+501'  },
  { code: 'BJ', name: 'Benin',                 flag: '🇧🇯', dial: '+229'  },
  { code: 'BT', name: 'Bhutan',                flag: '🇧🇹', dial: '+975'  },
  { code: 'BO', name: 'Bolivia',               flag: '🇧🇴', dial: '+591'  },
  { code: 'BA', name: 'Bosnia & Herzegovina',  flag: '🇧🇦', dial: '+387'  },
  { code: 'BW', name: 'Botswana',              flag: '🇧🇼', dial: '+267'  },
  { code: 'BR', name: 'Brazil',                flag: '🇧🇷', dial: '+55'   },
  { code: 'BN', name: 'Brunei',                flag: '🇧🇳', dial: '+673'  },
  { code: 'BG', name: 'Bulgaria',              flag: '🇧🇬', dial: '+359'  },
  { code: 'BF', name: 'Burkina Faso',          flag: '🇧🇫', dial: '+226'  },
  { code: 'BI', name: 'Burundi',               flag: '🇧🇮', dial: '+257'  },
  { code: 'CV', name: 'Cabo Verde',            flag: '🇨🇻', dial: '+238'  },
  { code: 'KH', name: 'Cambodia',              flag: '🇰🇭', dial: '+855'  },
  { code: 'CM', name: 'Cameroon',              flag: '🇨🇲', dial: '+237'  },
  { code: 'CA', name: 'Canada',                flag: '🇨🇦', dial: '+1'    },
  { code: 'CF', name: 'Central African Republic', flag: '🇨🇫', dial: '+236' },
  { code: 'TD', name: 'Chad',                  flag: '🇹🇩', dial: '+235'  },
  { code: 'CL', name: 'Chile',                 flag: '🇨🇱', dial: '+56'   },
  { code: 'CN', name: 'China',                 flag: '🇨🇳', dial: '+86'   },
  { code: 'CO', name: 'Colombia',              flag: '🇨🇴', dial: '+57'   },
  { code: 'KM', name: 'Comoros',               flag: '🇰🇲', dial: '+269'  },
  { code: 'CD', name: 'Congo (DR)',             flag: '🇨🇩', dial: '+243'  },
  { code: 'CG', name: 'Congo (Republic)',       flag: '🇨🇬', dial: '+242'  },
  { code: 'CR', name: 'Costa Rica',            flag: '🇨🇷', dial: '+506'  },
  { code: 'HR', name: 'Croatia',               flag: '🇭🇷', dial: '+385'  },
  { code: 'CU', name: 'Cuba',                  flag: '🇨🇺', dial: '+53'   },
  { code: 'CY', name: 'Cyprus',                flag: '🇨🇾', dial: '+357'  },
  { code: 'CZ', name: 'Czech Republic',        flag: '🇨🇿', dial: '+420'  },
  { code: 'DK', name: 'Denmark',               flag: '🇩🇰', dial: '+45'   },
  { code: 'DJ', name: 'Djibouti',              flag: '🇩🇯', dial: '+253'  },
  { code: 'DO', name: 'Dominican Republic',    flag: '🇩🇴', dial: '+1'    },
  { code: 'EC', name: 'Ecuador',               flag: '🇪🇨', dial: '+593'  },
  { code: 'EG', name: 'Egypt',                 flag: '🇪🇬', dial: '+20'   },
  { code: 'SV', name: 'El Salvador',           flag: '🇸🇻', dial: '+503'  },
  { code: 'GQ', name: 'Equatorial Guinea',     flag: '🇬🇶', dial: '+240'  },
  { code: 'ER', name: 'Eritrea',               flag: '🇪🇷', dial: '+291'  },
  { code: 'EE', name: 'Estonia',               flag: '🇪🇪', dial: '+372'  },
  { code: 'SZ', name: 'Eswatini',              flag: '🇸🇿', dial: '+268'  },
  { code: 'ET', name: 'Ethiopia',              flag: '🇪🇹', dial: '+251'  },
  { code: 'FJ', name: 'Fiji',                  flag: '🇫🇯', dial: '+679'  },
  { code: 'FI', name: 'Finland',               flag: '🇫🇮', dial: '+358'  },
  { code: 'FR', name: 'France',                flag: '🇫🇷', dial: '+33'   },
  { code: 'GA', name: 'Gabon',                 flag: '🇬🇦', dial: '+241'  },
  { code: 'GM', name: 'Gambia',                flag: '🇬🇲', dial: '+220'  },
  { code: 'GE', name: 'Georgia',               flag: '🇬🇪', dial: '+995'  },
  { code: 'DE', name: 'Germany',               flag: '🇩🇪', dial: '+49'   },
  { code: 'GH', name: 'Ghana',                 flag: '🇬🇭', dial: '+233'  },
  { code: 'GR', name: 'Greece',                flag: '🇬🇷', dial: '+30'   },
  { code: 'GT', name: 'Guatemala',             flag: '🇬🇹', dial: '+502'  },
  { code: 'GN', name: 'Guinea',                flag: '🇬🇳', dial: '+224'  },
  { code: 'GW', name: 'Guinea-Bissau',         flag: '🇬🇼', dial: '+245'  },
  { code: 'GY', name: 'Guyana',                flag: '🇬🇾', dial: '+592'  },
  { code: 'HT', name: 'Haiti',                 flag: '🇭🇹', dial: '+509'  },
  { code: 'HN', name: 'Honduras',              flag: '🇭🇳', dial: '+504'  },
  { code: 'HU', name: 'Hungary',               flag: '🇭🇺', dial: '+36'   },
  { code: 'IS', name: 'Iceland',               flag: '🇮🇸', dial: '+354'  },
  { code: 'IN', name: 'India',                 flag: '🇮🇳', dial: '+91'   },
  { code: 'ID', name: 'Indonesia',             flag: '🇮🇩', dial: '+62'   },
  { code: 'IR', name: 'Iran',                  flag: '🇮🇷', dial: '+98'   },
  { code: 'IQ', name: 'Iraq',                  flag: '🇮🇶', dial: '+964'  },
  { code: 'IE', name: 'Ireland',               flag: '🇮🇪', dial: '+353'  },
  { code: 'IL', name: 'Israel',                flag: '🇮🇱', dial: '+972'  },
  { code: 'IT', name: 'Italy',                 flag: '🇮🇹', dial: '+39'   },
  { code: 'JM', name: 'Jamaica',               flag: '🇯🇲', dial: '+1'    },
  { code: 'JP', name: 'Japan',                 flag: '🇯🇵', dial: '+81'   },
  { code: 'JO', name: 'Jordan',                flag: '🇯🇴', dial: '+962'  },
  { code: 'KZ', name: 'Kazakhstan',            flag: '🇰🇿', dial: '+7'    },
  { code: 'KE', name: 'Kenya',                 flag: '🇰🇪', dial: '+254'  },
  { code: 'KW', name: 'Kuwait',                flag: '🇰🇼', dial: '+965'  },
  { code: 'KG', name: 'Kyrgyzstan',            flag: '🇰🇬', dial: '+996'  },
  { code: 'LA', name: 'Laos',                  flag: '🇱🇦', dial: '+856'  },
  { code: 'LV', name: 'Latvia',                flag: '🇱🇻', dial: '+371'  },
  { code: 'LB', name: 'Lebanon',               flag: '🇱🇧', dial: '+961'  },
  { code: 'LS', name: 'Lesotho',               flag: '🇱🇸', dial: '+266'  },
  { code: 'LR', name: 'Liberia',               flag: '🇱🇷', dial: '+231'  },
  { code: 'LY', name: 'Libya',                 flag: '🇱🇾', dial: '+218'  },
  { code: 'LI', name: 'Liechtenstein',         flag: '🇱🇮', dial: '+423'  },
  { code: 'LT', name: 'Lithuania',             flag: '🇱🇹', dial: '+370'  },
  { code: 'LU', name: 'Luxembourg',            flag: '🇱🇺', dial: '+352'  },
  { code: 'MG', name: 'Madagascar',            flag: '🇲🇬', dial: '+261'  },
  { code: 'MW', name: 'Malawi',                flag: '🇲🇼', dial: '+265'  },
  { code: 'MY', name: 'Malaysia',              flag: '🇲🇾', dial: '+60'   },
  { code: 'MV', name: 'Maldives',              flag: '🇲🇻', dial: '+960'  },
  { code: 'ML', name: 'Mali',                  flag: '🇲🇱', dial: '+223'  },
  { code: 'MT', name: 'Malta',                 flag: '🇲🇹', dial: '+356'  },
  { code: 'MR', name: 'Mauritania',            flag: '🇲🇷', dial: '+222'  },
  { code: 'MU', name: 'Mauritius',             flag: '🇲🇺', dial: '+230'  },
  { code: 'MX', name: 'Mexico',                flag: '🇲🇽', dial: '+52'   },
  { code: 'MD', name: 'Moldova',               flag: '🇲🇩', dial: '+373'  },
  { code: 'MC', name: 'Monaco',                flag: '🇲🇨', dial: '+377'  },
  { code: 'MN', name: 'Mongolia',              flag: '🇲🇳', dial: '+976'  },
  { code: 'ME', name: 'Montenegro',            flag: '🇲🇪', dial: '+382'  },
  { code: 'MA', name: 'Morocco',               flag: '🇲🇦', dial: '+212'  },
  { code: 'MZ', name: 'Mozambique',            flag: '🇲🇿', dial: '+258'  },
  { code: 'MM', name: 'Myanmar',               flag: '🇲🇲', dial: '+95'   },
  { code: 'NA', name: 'Namibia',               flag: '🇳🇦', dial: '+264'  },
  { code: 'NP', name: 'Nepal',                 flag: '🇳🇵', dial: '+977'  },
  { code: 'NL', name: 'Netherlands',           flag: '🇳🇱', dial: '+31'   },
  { code: 'NZ', name: 'New Zealand',           flag: '🇳🇿', dial: '+64'   },
  { code: 'NI', name: 'Nicaragua',             flag: '🇳🇮', dial: '+505'  },
  { code: 'NE', name: 'Niger',                 flag: '🇳🇪', dial: '+227'  },
  { code: 'NG', name: 'Nigeria',               flag: '🇳🇬', dial: '+234'  },
  { code: 'NO', name: 'Norway',                flag: '🇳🇴', dial: '+47'   },
  { code: 'OM', name: 'Oman',                  flag: '🇴🇲', dial: '+968'  },
  { code: 'PK', name: 'Pakistan',              flag: '🇵🇰', dial: '+92'   },
  { code: 'PA', name: 'Panama',                flag: '🇵🇦', dial: '+507'  },
  { code: 'PG', name: 'Papua New Guinea',      flag: '🇵🇬', dial: '+675'  },
  { code: 'PY', name: 'Paraguay',              flag: '🇵🇾', dial: '+595'  },
  { code: 'PE', name: 'Peru',                  flag: '🇵🇪', dial: '+51'   },
  { code: 'PH', name: 'Philippines',           flag: '🇵🇭', dial: '+63'   },
  { code: 'PL', name: 'Poland',                flag: '🇵🇱', dial: '+48'   },
  { code: 'PT', name: 'Portugal',              flag: '🇵🇹', dial: '+351'  },
  { code: 'QA', name: 'Qatar',                 flag: '🇶🇦', dial: '+974'  },
  { code: 'RO', name: 'Romania',               flag: '🇷🇴', dial: '+40'   },
  { code: 'RU', name: 'Russia',                flag: '🇷🇺', dial: '+7'    },
  { code: 'RW', name: 'Rwanda',                flag: '🇷🇼', dial: '+250'  },
  { code: 'SA', name: 'Saudi Arabia',          flag: '🇸🇦', dial: '+966'  },
  { code: 'SN', name: 'Senegal',               flag: '🇸🇳', dial: '+221'  },
  { code: 'RS', name: 'Serbia',                flag: '🇷🇸', dial: '+381'  },
  { code: 'SL', name: 'Sierra Leone',          flag: '🇸🇱', dial: '+232'  },
  { code: 'SG', name: 'Singapore',             flag: '🇸🇬', dial: '+65'   },
  { code: 'SK', name: 'Slovakia',              flag: '🇸🇰', dial: '+421'  },
  { code: 'SI', name: 'Slovenia',              flag: '🇸🇮', dial: '+386'  },
  { code: 'SO', name: 'Somalia',               flag: '🇸🇴', dial: '+252'  },
  { code: 'ZA', name: 'South Africa',          flag: '🇿🇦', dial: '+27'   },
  { code: 'SS', name: 'South Sudan',           flag: '🇸🇸', dial: '+211'  },
  { code: 'ES', name: 'Spain',                 flag: '🇪🇸', dial: '+34'   },
  { code: 'LK', name: 'Sri Lanka',             flag: '🇱🇰', dial: '+94'   },
  { code: 'SD', name: 'Sudan',                 flag: '🇸🇩', dial: '+249'  },
  { code: 'SR', name: 'Suriname',              flag: '🇸🇷', dial: '+597'  },
  { code: 'SE', name: 'Sweden',                flag: '🇸🇪', dial: '+46'   },
  { code: 'CH', name: 'Switzerland',           flag: '🇨🇭', dial: '+41'   },
  { code: 'SY', name: 'Syria',                 flag: '🇸🇾', dial: '+963'  },
  { code: 'TW', name: 'Taiwan',                flag: '🇹🇼', dial: '+886'  },
  { code: 'TJ', name: 'Tajikistan',            flag: '🇹🇯', dial: '+992'  },
  { code: 'TZ', name: 'Tanzania',              flag: '🇹🇿', dial: '+255'  },
  { code: 'TH', name: 'Thailand',              flag: '🇹🇭', dial: '+66'   },
  { code: 'TG', name: 'Togo',                  flag: '🇹🇬', dial: '+228'  },
  { code: 'TT', name: 'Trinidad & Tobago',     flag: '🇹🇹', dial: '+1'    },
  { code: 'TN', name: 'Tunisia',               flag: '🇹🇳', dial: '+216'  },
  { code: 'TR', name: 'Turkey',                flag: '🇹🇷', dial: '+90'   },
  { code: 'TM', name: 'Turkmenistan',          flag: '🇹🇲', dial: '+993'  },
  { code: 'UG', name: 'Uganda',                flag: '🇺🇬', dial: '+256'  },
  { code: 'UA', name: 'Ukraine',               flag: '🇺🇦', dial: '+380'  },
  { code: 'AE', name: 'United Arab Emirates',  flag: '🇦🇪', dial: '+971'  },
  { code: 'GB', name: 'United Kingdom',        flag: '🇬🇧', dial: '+44'   },
  { code: 'US', name: 'United States',         flag: '🇺🇸', dial: '+1'    },
  { code: 'UY', name: 'Uruguay',               flag: '🇺🇾', dial: '+598'  },
  { code: 'UZ', name: 'Uzbekistan',            flag: '🇺🇿', dial: '+998'  },
  { code: 'VE', name: 'Venezuela',             flag: '🇻🇪', dial: '+58'   },
  { code: 'VN', name: 'Vietnam',               flag: '🇻🇳', dial: '+84'   },
  { code: 'YE', name: 'Yemen',                 flag: '🇾🇪', dial: '+967'  },
  { code: 'ZM', name: 'Zambia',                flag: '🇿🇲', dial: '+260'  },
  { code: 'ZW', name: 'Zimbabwe',              flag: '🇿🇼', dial: '+263'  },
];

/* ════════════════════════════════════════════════
   1. COUNTRY FLAG PICKER
   ════════════════════════════════════════════════ */
const picker       = document.getElementById('countryPicker');
const trigger      = document.getElementById('countryTrigger');
const dropdown     = document.getElementById('countryDropdown');
const searchInput  = document.getElementById('countrySearch');
const countryList  = document.getElementById('countryList');
const selectedFlag = document.getElementById('selectedFlag');
const selectedName = document.getElementById('selectedCountryName');
const countryHidden= document.getElementById('country');

// Phone badge elements
const dialBadge    = document.getElementById('phoneDialBadge');
const dialCodeText = document.getElementById('dialCodeText');
const phoneInput   = document.getElementById('phone_number');
const phoneHidden  = document.getElementById('phone_full');

// Hide badge initially (no country selected yet)
dialBadge.style.display = 'none';

let selectedCountry  = null;
let focusedIndex     = -1;

/* Helper: returns a flag <img> tag URL from flagcdn.com */
function flagUrl(code) {
  return `https://flagcdn.com/20x15/${code.toLowerCase()}.png`;
}
function flagImg(code, cls = '') {
  return `<img src="${flagUrl(code)}" class="${cls}" alt="" width="20" height="14" onerror="this.style.display='none'">`;
}

function renderList(filter = '') {
  const q = filter.trim().toLowerCase();
  const filtered = q
    ? COUNTRIES.filter(c => c.name.toLowerCase().includes(q) || c.dial.includes(q) || c.code.toLowerCase().includes(q))
    : COUNTRIES;

  countryList.innerHTML = '';
  focusedIndex = -1;

  if (!filtered.length) {
    countryList.innerHTML = '<li class="no-result">No country found</li>';
    return;
  }

  filtered.forEach((c, idx) => {
    const li = document.createElement('li');
    li.dataset.code = c.code;
    li.dataset.idx = idx;
    if (selectedCountry && selectedCountry.code === c.code) li.classList.add('selected');

    li.innerHTML = `
      ${flagImg(c.code, 'c-flag')}
      <span class="c-name">${c.name}</span>
      <span class="c-dial">${c.dial}</span>
    `;
    li.addEventListener('mousedown', e => {
      e.preventDefault();
      selectCountry(c);
    });
    countryList.appendChild(li);
  });
}

function selectCountry(c) {
  selectedCountry = c;

  // Update trigger — inject real flag image
  selectedFlag.innerHTML = flagImg(c.code, 'country-flag');
  selectedName.textContent = c.name;
  picker.classList.add('selected');

  // Update hidden field
  countryHidden.value = c.code;

  // Update phone dial badge — dial code only, no flag
  dialBadge.style.display = 'flex';
  dialCodeText.textContent = c.dial;
  dialBadge.classList.add('has-code');

  // Remove validation errors
  picker.classList.remove('invalid');

  closeDropdown();
  formatPhone();
}

function openDropdown() {
  picker.classList.add('open');
  picker.setAttribute('aria-expanded', 'true');
  renderList(searchInput.value);
  // Scroll to selected
  requestAnimationFrame(() => {
    const sel = countryList.querySelector('.selected');
    if (sel) sel.scrollIntoView({ block: 'nearest' });
    searchInput.focus();
  });
}

function closeDropdown() {
  picker.classList.remove('open');
  picker.setAttribute('aria-expanded', 'false');
  searchInput.value = '';
}

// Toggle on trigger click
trigger.addEventListener('click', e => {
  e.stopPropagation();
  picker.classList.contains('open') ? closeDropdown() : openDropdown();
});

// Filter while searching
searchInput.addEventListener('input', () => {
  renderList(searchInput.value);
  focusedIndex = -1;
});

// Keyboard navigation in list
searchInput.addEventListener('keydown', e => {
  const items = countryList.querySelectorAll('li:not(.no-result)');
  if (!items.length) return;

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    focusedIndex = Math.min(focusedIndex + 1, items.length - 1);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    focusedIndex = Math.max(focusedIndex - 1, 0);
  } else if (e.key === 'Enter' && focusedIndex >= 0) {
    e.preventDefault();
    const code = items[focusedIndex].dataset.code;
    const found = COUNTRIES.find(c => c.code === code);
    if (found) selectCountry(found);
    return;
  } else if (e.key === 'Escape') {
    closeDropdown();
    return;
  }

  items.forEach((li, i) => li.classList.toggle('focused', i === focusedIndex));
  if (focusedIndex >= 0) items[focusedIndex].scrollIntoView({ block: 'nearest' });
});

// Close when clicking outside
document.addEventListener('click', e => {
  if (!picker.contains(e.target)) closeDropdown();
});

// Initial render
renderList();


/* ════════════════════════════════════════════════
   2. AUTO-FORMAT NUMÉRO DE TÉLÉPHONE
   ════════════════════════════════════════════════ */
function formatPhone() {
  if (!selectedCountry) return;
  const raw = phoneInput.value.replace(/\D/g, ''); // digits only
  phoneHidden.value = selectedCountry.dial + raw;
}

phoneInput.addEventListener('input', () => {
  // Strip non-digit chars as user types
  const cursor = phoneInput.selectionStart;
  const clean = phoneInput.value.replace(/[^\d\s\-\(\)\.]/g, '');
  if (phoneInput.value !== clean) {
    phoneInput.value = clean;
    phoneInput.setSelectionRange(cursor - 1, cursor - 1);
  }
  formatPhone();
  // Remove invalid state while typing
  if (phoneInput.value) phoneInput.classList.remove('invalid');
});

phoneInput.addEventListener('blur', () => {
  formatPhone();
  if (!phoneInput.value.trim()) phoneInput.classList.add('invalid');
  else phoneInput.classList.remove('invalid');
});


/* ════════════════════════════════════════════════
   3. JAUGE MOT DE PASSE
   ════════════════════════════════════════════════ */
const pwdInput      = document.getElementById('password');
const confirmPwd    = document.getElementById('confirm_password');
const pwdMeterBar   = document.getElementById('pwd-meter-bar');
const pwdMeterText  = document.getElementById('pwd-meter-text');
const pwdToggle     = document.getElementById('pwdToggle');

function updatePwdMeter(val) {
  let score = 0;
  if (val.length > 5)  score++;
  if (val.length > 8)  score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  let width = '0%', color = '#ef476f', text = '';

  if (!val.length) {
    width = '0%'; text = '';
  } else if (score <= 2) {
    width = '33%'; color = '#ef476f'; text = 'Weak';
  } else if (score <= 4) {
    width = '66%'; color = '#ffd166'; text = 'Medium';
  } else {
    width = '100%'; color = '#06d6a0'; text = 'Strong';
  }

  pwdMeterBar.style.width  = width;
  pwdMeterBar.style.background = color;
  pwdMeterText.textContent = text;
  pwdMeterText.style.color = color;
}

pwdInput.addEventListener('input', () => {
  updatePwdMeter(pwdInput.value);
  if (confirmPwd.value) validateInput(confirmPwd);
});

// Show/hide password toggle
pwdToggle.addEventListener('click', () => {
  const isPass = pwdInput.type === 'password';
  pwdInput.type = isPass ? 'text' : 'password';
  pwdToggle.querySelector('svg').innerHTML = isPass
    ? '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>'
    : '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
});


/* ════════════════════════════════════════════════
   4. VALIDATION EN TEMPS RÉEL
   ════════════════════════════════════════════════ */
const form   = document.getElementById('demoForm');
const inputs = form.querySelectorAll('input[required]:not([type="hidden"])');

function validateInput(input) {
  let isValid = true;
  const val = input.value.trim();

  if (!val) {
    isValid = false;
  } else if (input.type === 'email') {
    isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  } else if (input.id === 'password') {
    isValid = val.length >= 8;
  } else if (input.id === 'confirm_password') {
    isValid = val === pwdInput.value;
  }

  input.classList.toggle('invalid', !isValid);
  return isValid;
}

inputs.forEach(input => {
  input.addEventListener('input', () => {
    if (input.classList.contains('invalid') || input.id === 'confirm_password') {
      validateInput(input);
    }
  });
  input.addEventListener('blur', () => validateInput(input));
});


/* ════════════════════════════════════════════════
   5. SOUMISSION DU FORMULAIRE
   ════════════════════════════════════════════════ */
form.addEventListener('submit', function(e) {
  let formValid = true;

  // Validate all inputs
  inputs.forEach(input => { if (!validateInput(input)) formValid = false; });

  // Validate country
  if (!countryHidden.value) {
    picker.classList.add('invalid');
    formValid = false;
  }

  // Validate phone
  if (!phoneInput.value.trim()) {
    phoneInput.classList.add('invalid');
    formValid = false;
  }

  // Build full phone number before submit
  formatPhone();

  if (!formValid) {
    e.preventDefault();
    // Scroll to first error
    const firstInvalid = form.querySelector('.invalid, [aria-invalid="true"]');
    if (firstInvalid) firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  // Submit animation
  const btn = document.getElementById('submitBtn');
  btn.innerHTML = `<span style="display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin 1s linear infinite;"></span>&nbsp;Processing...`;
  btn.disabled = true;
});


/* ════════════════════════════════════════════════
   6. ANIMATION BRAIN CANVAS (ARRIÈRE-PLAN)
   ════════════════════════════════════════════════ */
(function () {
  const canvas = document.getElementById('brainCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const P = [124, 92, 252];
  const T = [6, 214, 160];

  function rgb(c, a)    { return `rgba(${c[0]},${c[1]},${c[2]},${+a.toFixed(3)})`; }
  function mix(a, b, t) { return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t]; }
  function lp(a, b, t)  { return a+(b-a)*t; }
  function eo(t, e=3)   { return 1-Math.pow(1-Math.min(t,1),e); }
  function clamp(v,lo,hi){ return Math.max(lo,Math.min(hi,v)); }
  function rand(a, b)   { return a+Math.random()*(b-a); }

  let W, H;
  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }

  const PH_BANG=0, PH_FLY=1000, PH_SETTLE=2000;
  let nodes=[], startT=null, raf;
  let mouse={x:-9999,y:-9999};

  function connR() { return Math.hypot(W,H)*0.15; }

  function mkNode() {
    const pad=50;
    const tx=rand(pad,W-pad), ty=rand(pad,H-pad);
    const cx=W*.5, cy=H*.5;
    const ang=Math.atan2(ty-cy,tx-cx)+rand(-0.35,0.35);
    const spd=rand(5,14);
    return {
      x:cx, y:cy, vx:Math.cos(ang)*spd, vy:Math.sin(ang)*spd,
      tx, ty, r:rand(1.4,3.8), hue:Math.random(),
      ph:rand(0,Math.PI*2), phSpd:rand(0.007,0.022),
      bright:rand(0.5,1.0), wAng:rand(0,Math.PI*2),
      wSpd:rand(0.0003,0.0008), trail:[], isPlanet:false,
    };
  }

  function init() {
    nodes = Array.from({length:140}, mkNode);
    startT = null;
    const pCount=7;
    const pIdx=[...Array(nodes.length).keys()].sort(()=>Math.random()-.5).slice(0,pCount);
    pIdx.forEach((i,k) => {
      const n=nodes[i];
      n.isPlanet=true; n.r=rand(4.5,8.5); n.bright=1.0;
      const ang2=(k/pCount)*Math.PI*2+rand(-.3,.3);
      const dist=Math.min(W,H)*0.32;
      n.tx=W*.5+Math.cos(ang2)*dist; n.ty=H*.5+Math.sin(ang2)*dist;
    });
    for (const n of nodes) { n.x=n.tx; n.y=n.ty; }
  }

  function draw(ts) {
    if (!startT) startT=ts;
    const t=ts-startT+5000;
    const cx=W*.5, cy=H*.5;
    ctx.clearRect(0,0,W,H);

    const fly=clamp((t-PH_BANG)/(PH_FLY-PH_BANG),0,1);
    const setP=clamp((t-PH_FLY)/(PH_SETTLE-PH_FLY),0,1);

    for (const n of nodes) {
      n.ph+=n.phSpd;
      if (n.trail.length>0) n.trail.shift();
      n.wAng+=n.wSpd*(1+.3*Math.sin(n.ph));
      const wF=n.isPlanet?0.003:0.005;
      n.vx+=Math.cos(n.wAng)*wF; n.vy+=Math.sin(n.wAng)*wF;

      if (!n.isPlanet) {
        let nearP=null, nearD2=Infinity;
        for (const p of nodes) {
          if (!p.isPlanet) continue;
          const gx=p.x-n.x, gy=p.y-n.y, gd2=gx*gx+gy*gy;
          if (gd2<nearD2) { nearD2=gd2; nearP=p; }
        }
        if (nearP) {
          const gd=Math.sqrt(nearD2)||1;
          n.vx+=(nearP.x-n.x)/gd*0.003; n.vy+=(nearP.y-n.y)/gd*0.003;
          n.vx+=-(nearP.y-n.y)/gd*0.006; n.vy+=(nearP.x-n.x)/gd*0.006;
        }
      } else {
        const cdx=cx-n.x, cdy=cy-n.y, cd=Math.hypot(cdx,cdy)||1;
        if (cd>Math.min(W,H)*0.3) { n.vx+=(cdx/cd)*0.002; n.vy+=(cdy/cd)*0.002; }
      }

      const mdx=n.x-mouse.x, mdy=n.y-mouse.y, md2=mdx*mdx+mdy*mdy;
      if (md2<22000) { const f=.6/Math.max(md2,1); n.vx+=mdx*f; n.vy+=mdy*f; }

      const pad=40;
      if (n.x<pad) n.vx+=(pad-n.x)*.01;
      if (n.x>W-pad) n.vx-=(n.x-(W-pad))*.01;
      if (n.y<pad) n.vy+=(pad-n.y)*.01;
      if (n.y>H-pad) n.vy-=(n.y-(H-pad))*.01;

      n.vx*=.991; n.vy*=.991; n.x+=n.vx; n.y+=n.vy;
    }

    const cA=lp(0,0.13,eo(setP,3)), cR=connR();
    for (let i=0;i<nodes.length;i++) {
      const a=nodes[i];
      for (let j=i+1;j<nodes.length;j++) {
        const b=nodes[j];
        const dx=b.x-a.x, dy=b.y-a.y, d2=dx*dx+dy*dy;
        if (d2>cR*cR) continue;
        const d=Math.sqrt(d2);
        ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y);
        ctx.strokeStyle=rgb(mix(P,T,(a.hue+b.hue)*.5),cA*(1-d/cR));
        ctx.lineWidth=.7; ctx.stroke();
      }
    }

    for (const n of nodes) {
      const col=mix(P,T,n.hue);
      const pul=.55+.45*Math.sin(n.ph);
      const r=n.r*(.88+.12*pul);
      const al=n.bright*pul*.9;
      if (n.isPlanet) {
        const g2=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*18);
        g2.addColorStop(0,rgb(col,al*.35)); g2.addColorStop(.5,rgb(col,al*.1)); g2.addColorStop(1,rgb(col,0));
        ctx.beginPath(); ctx.arc(n.x,n.y,r*18,0,Math.PI*2); ctx.fillStyle=g2; ctx.fill();
        ctx.beginPath(); ctx.arc(n.x,n.y,r*1.6,0,Math.PI*2); ctx.fillStyle=rgb(col,al*.9); ctx.fill();
        ctx.beginPath(); ctx.arc(n.x,n.y,r*1.6,0,Math.PI*2); ctx.strokeStyle=rgb(col,.25); ctx.lineWidth=r*.6; ctx.stroke();
      } else {
        const g=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*6);
        g.addColorStop(0,rgb(col,al*.4)); g.addColorStop(1,rgb(col,0));
        ctx.beginPath(); ctx.arc(n.x,n.y,r*6,0,Math.PI*2); ctx.fillStyle=g; ctx.fill();
        ctx.beginPath(); ctx.arc(n.x,n.y,r,0,Math.PI*2); ctx.fillStyle=rgb(col,al); ctx.fill();
      }
    }

    raf=requestAnimationFrame(draw);
  }

  document.addEventListener('mousemove', e => { mouse.x=e.clientX; mouse.y=e.clientY; }, {passive:true});
  document.addEventListener('mouseleave', () => { mouse.x=-9999; mouse.y=-9999; });

  function start() { resize(); init(); raf=requestAnimationFrame(draw); }
  window.addEventListener('resize', () => { cancelAnimationFrame(raf); start(); });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else { startT=null; raf=requestAnimationFrame(draw); }
  });
  start();
})();
