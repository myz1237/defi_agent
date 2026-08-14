> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# EVM Providers

> A list of providers/tools LI.FI aggregates

export const EvmTools = () => {
  const [chains, setChains] = useState(null);
  const [tools, setTools] = useState(null);
  const [error, setError] = useState(null);
  useEffect(() => {
    const fetchChains = async () => {
      try {
        const response = await fetch('https://li.quest/v1/chains?chainTypes=EVM,SVM,UTXO,MVM,TVM');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData = await response.json();
        setChains(jsonData.chains);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchChains();
  }, []);
  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await fetch('https://li.quest/v1/tools');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const jsonData = await response.json();
        setTools(jsonData);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchTools();
  }, []);
  const parseBridges = (bridges, chains) => bridges.map(bridge => {
    const fromChainIds = bridge.supportedChains.map(connection => connection.fromChainId);
    const toChainIds = bridge.supportedChains.map(connection => connection.toChainId);
    const connectedChains = [...new Set([...fromChainIds, ...toChainIds])].map(chainId => chains.find(chain => chain.id === chainId)).sort((a, b) => a.id - b.id).filter(chain => !!chain);
    return {
      ...bridge,
      fromChainIds,
      toChainIds,
      connectedChains
    };
  }).filter(bridge => bridge.connectedChains.length).sort((a, b) => b.connectedChains.length - a.connectedChains.length);
  const parseExchanges = (exchanges, chains) => exchanges.map(exchange => ({
    ...exchange,
    supportedChains: exchange.supportedChains.map(chainId => chains.find(chain => chain.id === chainId)).sort((a, b) => a.id - b.id).filter(chain => chain?.chainType === "EVM")
  })).filter(exchange => exchange.supportedChains.length > 0).sort((a, b) => b.supportedChains.length - a.supportedChains.length + a.supportedChains[0].id / 1000 - b.supportedChains[0].id / 1000);
  const renderChains = chains => <div className="p-2">
      <div className="flex flex-wrap gap-4">
        {chains.map(chain => <div key={chain.key} className="relative group flex-shrink-0">
            <img src={chain.logoURI} alt={chain.name} className="w-5 h-5 rounded-full object-cover not-prose" />
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
              {chain.name}
            </div>
          </div>)}
      </div>
    </div>;
  const exchangesOnChain = (exchanges, chain) => exchanges.filter(exchange => exchange.supportedChains.some(supportedChainId => supportedChainId === chain.id));
  const bridgesOnChain = (bridges, chain) => bridges.filter(bridge => bridge.supportedChains.some(({fromChainId, toChainId}) => fromChainId === chain.id || toChainId === chain.id));
  const renderTools = (tools, chains) => {
    const bridges = parseBridges(tools.bridges, chains);
    const exchanges = parseExchanges(tools.exchanges, chains);
    return <div>
      <h2>Supported Bridges</h2>
      <table className="p-3">
        <thead>
          <tr>
            <th className="w-6"></th>
            <th className="text-left"><strong>Bridge Name</strong></th>
            <th><strong>Key</strong></th>
            <th className="text-left"><strong>Supported Chains</strong></th>
          </tr>
        </thead>
        <tbody>
          {bridges.map(bridge => <tr key={bridge.key}>
              <td>
                <img src={bridge.logoURI} alt={bridge.name} className="w-3 h-3 rounded-full not-prose" />
              </td>
              <td><strong>{bridge.name}</strong></td>
              <td><code>{bridge.key}</code></td>
              <td>{renderChains(bridge.connectedChains)}</td>
            </tr>)}
        </tbody>
      </table>

      <h2>Supported Exchanges</h2>
      <table className="p-3">
        <thead>
          <tr>
            <th className="w-6"></th>
            <th className="text-left"><strong>Exchange Name</strong></th>
            <th><strong>Key</strong></th>
            <th className="text-left"><strong>Supported Chains</strong></th>
          </tr>
        </thead>
        <tbody>
          {exchanges.map(exchange => <tr key={exchange.key}>
              <td>
                <img src={exchange.logoURI} alt={exchange.name} className="w-3 h-3 rounded-full not-prose" />
              </td>
              <td><strong>{exchange.name}</strong></td>
              <td><code>{exchange.key}</code></td>
              <td>{renderChains(exchange.supportedChains)}</td>
            </tr>)}
        </tbody>
      </table>


      <h2>By Chain</h2>
      <table className="p-3">
        <thead>
          <tr>
            <th className="w-6"></th>
            <th className="text-left"><strong>Chain Name</strong></th>
            <th><strong>Chain Id</strong></th>
            <th className="text-left"><strong>Supported Bridges</strong></th>
            <th className="text-left"><strong>Supported Exchanges</strong></th>
          </tr>
        </thead>
        <tbody>
          {chains.filter(chain => chain.chainType === 'EVM').map(chain => <tr key={chain.key}>
              <td>
                <img src={chain.logoURI} alt={chain.name} className="w-3 h-3 rounded-full not-prose" />
              </td>
              <td><strong>{chain.name}</strong></td>
              <td><code>{chain.id}</code></td>
              <td>{bridgesOnChain(tools.bridges, chain).map(e => e.key).join(', ') || '-'}</td>
              <td>{exchangesOnChain(tools.exchanges, chain).map(e => e.key).join(', ') || '-'}</td>
            </tr>)}
        </tbody>
      </table>
    </div>;
  };
  if (error) return <div>Error: {error}</div>; else if (chains && tools) return renderTools(tools, chains); else return <div>Loading...</div>;
};

<EvmTools />

The list of supported tools can also be found on our [API](/api-reference/get-available-bridges-and-exchanges).
