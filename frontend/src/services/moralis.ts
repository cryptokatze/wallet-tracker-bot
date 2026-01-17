import type { Chain, Token } from '@/types';

// Moralis 체인 ID 매핑
const MORALIS_CHAIN_IDS: Record<Chain, string> = {
  ethereum: '0x1',
  bsc: '0x38',
  polygon: '0x89',
  arbitrum: '0xa4b1',
  optimism: '0xa',
  avalanche: '0xa86a',
  base: '0x2105',
};

// API 키 가져오기
const getMoralisApiKey = (): string => {
  const key = import.meta.env.VITE_MORALIS_API_KEY;
  if (!key) {
    console.error('[Moralis] API 키가 설정되지 않았습니다. .env 파일에 VITE_MORALIS_API_KEY를 추가하세요.');
  }
  return key || '';
};

// Moralis API 응답 타입
interface MoralisTokenBalance {
  token_address: string;
  symbol: string;
  name: string;
  logo: string | null;
  thumbnail: string | null;
  decimals: number;
  balance: string;
  possible_spam: boolean;
  verified_contract: boolean;
  usd_price: number | null;
  usd_price_24hr_percent_change: number | null;
  usd_price_24hr_usd_change: number | null;
  usd_value: number | null;
  native_token: boolean;
  portfolio_percentage: number;
}

interface MoralisResponse {
  result: MoralisTokenBalance[];
}

// 지갑 토큰 잔액 조회 (가격 포함)
export async function getWalletTokenBalances(
  address: string,
  chain: Chain
): Promise<Token[]> {
  const apiKey = getMoralisApiKey();
  const chainId = MORALIS_CHAIN_IDS[chain];

  // 주소 정규화 (소문자로 변환, Moralis는 대소문자 무관)
  const normalizedAddress = address.trim().toLowerCase();

  // 기본 형식 검증 (0x + 40자리 16진수) - 소문자 변환 후이므로 [a-f0-9]만 체크
  if (!/^0x[a-f0-9]{40}$/.test(normalizedAddress)) {
    console.error(`[Moralis] 잘못된 주소 형식: ${address}`);
    throw new Error('잘못된 지갑 주소 형식입니다');
  }

  console.log(`[Moralis] ${chain} 토큰 잔액 조회 시작: ${normalizedAddress}`);

  try {
    const url = `https://deep-index.moralis.io/api/v2.2/wallets/${normalizedAddress}/tokens?chain=${chainId}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[Moralis] API 에러: ${response.status}`, errorText);
      throw new Error(`Moralis API 에러: ${response.status}`);
    }

    const data: MoralisResponse = await response.json();
    console.log(`[Moralis] ${chain} 토큰 수: ${data.result?.length || 0}`);

    // 스팸 토큰 필터링 및 변환
    const tokens: Token[] = (data.result || [])
      .filter((t) => !t.possible_spam)
      .filter((t) => {
        const balance = Number(t.balance) / Math.pow(10, t.decimals);
        // 잔액이 0.0001 이상이거나 USD 가치가 $0.01 이상인 토큰만
        return balance > 0.0001 || (t.usd_value && t.usd_value > 0.01);
      })
      .map((t) => {
        const formattedBalance = Number(t.balance) / Math.pow(10, t.decimals);
        return {
          symbol: t.symbol,
          name: t.name,
          address: t.native_token ? 'native' : t.token_address,
          chain,
          decimals: t.decimals,
          balance: t.balance,
          formattedBalance,
          priceUsd: t.usd_price || 0,
          valueUsd: t.usd_value || formattedBalance * (t.usd_price || 0),
          logoUrl: t.logo || t.thumbnail || undefined,
          priceChange24h: t.usd_price_24hr_percent_change || undefined,
          isNative: t.native_token,
          isVerified: t.verified_contract,
        };
      })
      // 가치 순으로 정렬
      .sort((a, b) => b.valueUsd - a.valueUsd);

    console.log(`[Moralis] ${chain} 최종 토큰 목록:`, tokens.map((t) => `${t.symbol}: $${t.valueUsd.toFixed(2)}`));
    return tokens;
  } catch (error) {
    console.error(`[Moralis] ${chain} 토큰 조회 실패:`, error);
    throw error;
  }
}

// 여러 체인에서 동시에 조회
export async function getMultiChainTokenBalances(
  address: string,
  chains: Chain[]
): Promise<{ chain: Chain; tokens: Token[]; error?: string }[]> {
  console.log(`[Moralis] 멀티체인 조회 시작: ${chains.join(', ')}`);

  const results = await Promise.all(
    chains.map(async (chain) => {
      try {
        const tokens = await getWalletTokenBalances(address, chain);
        return { chain, tokens };
      } catch (error) {
        console.error(`[Moralis] ${chain} 조회 실패:`, error);
        return { chain, tokens: [], error: (error as Error).message };
      }
    })
  );

  return results;
}
