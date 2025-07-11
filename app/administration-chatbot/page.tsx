'use client';

import {
  Box,
  Input,
  Button,
  VStack,
  Text,
  Flex,
  Icon,
  Image,
  InputGroup,
  InputLeftElement,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  HStack,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure
} from '@chakra-ui/react';
import {
  IoArrowBack,
  IoLogOut,
  IoSend,
  IoSearch,
  IoPersonCircle,
  IoCopy,
  IoRefresh,
  IoBarChart,
  IoChatbubbles
} from 'react-icons/io5';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

export default function AdministrationChatbotPage() {
  // All chat histories state
  const [allChats, setAllChats] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  // Chatbot size toggle state
  const [isChatbotLarge, setIsChatbotLarge] = useState(false);
  const helpText = `Voici tout ce que je peux faire pour toi :\n📊 Donne-moi le feedback chart.\n🟢🔴😐 Afficher le détail des feedbacks positifs, négatifs ou neutres\nsur une période donnée ou par matière.\n📈 Afficher des\ngraphiques\n(camembert, barres, donut) pour toutes les matières ou une matière précise.\n⚖️ Comparer plusieurs matières sur leurs feedbacks (nombre, positifs, négatifs, neutres).\n🏆 Afficher le top N matières\nayant reçu le plus de feedbacks sur une période.\n🤖 Répondre à toutes tes questions sur les statistiques de feedbacks étudiants.\n\nTu peux essayer par exemple :\n• 👉 « Afficher les details de feedbacks positifs aujourd'hui. »\n• 👉 « Afficher les details de feedbacks pour la matière machine learning. »\n• 👉 « Donne-moi les feedbacks négatifs cette semaine. »\n• 👉 « Affiche moi des graphiques pour la matiere machine learning et la matiere business.»\n• 👉 « Donne-moi les graphiques des feedbacks pour la matière finance hier. »\n• 👉 « Donne moi les top 3 matières de cette semaine. »\n• 👉 « Donne-moi le chart comparatif des feedbacks par matière. »`;
  const { isOpen, onOpen, onClose } = useDisclosure();
  const router = useRouter();
  const toast = useToast();
  const [messages, setMessages] = useState<{ text: string; sender: 'bot' | 'user' }[]>([]);
  const [input, setInput] = useState('');
  const [agentActive, setAgentActive] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([{ text: "Bonjour, comment puis-je vous aider en tant qu'administrateur ?", sender: 'bot' }]);
  }, []);

  // Fetch chat history on mount (like admin_chat.html)
  useEffect(() => {
    fetch(`http://127.0.0.1:5000/api/student-messages/all`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data)) {
          setAllChats(data);
        }
      })
      .catch(() => {
        setAllChats([]);
      });
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const handleExampleClick = (example: string) => {
    setInput(example);
    setTimeout(() => handleSend(example), 0);
  };

  const handleSend = async (overrideInput?: string) => {
    const messageToSend = overrideInput || input;
    if (!messageToSend.trim()) return;

    setMessages(prev => [...prev, { text: messageToSend, sender: 'user' }]);
    setInput('');
    setAgentActive(true);

    toast({
      title: 'Generating response...',
      status: 'info',
      duration: 2000,
      isClosable: true
    });

    setTimeout(async () => {
      try {
        const res = await axios.post(
          'http://127.0.0.1:5000/admin/api/chat',
          { message: messageToSend },
          { withCredentials: true }
        );
        setMessages(prev => [...prev, { text: res.data.response, sender: 'bot' }]);
      } catch {
        setMessages(prev => [...prev, { text: 'Error: Unable to connect to backend.', sender: 'bot' }]);
      } finally {
        setAgentActive(false);
        toast.closeAll();
      }
    }, 2000);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Message Copied',
      description: 'The message has been copied to your clipboard.',
      status: 'success',
      duration: 2000,
      isClosable: true,
      position: 'top'
    });
  };

  const handleRefresh = () => {
    toast({
      title: 'Refreshing...',
      description: 'The answer will be refreshed soon.',
      status: 'info',
      duration: 1800,
      isClosable: true,
      position: 'top'
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('authenticated');
    router.push('/administration-login');
  };

  return (
    <Flex w="100vw" h="100vh" overflow="hidden">
      {/* Sidebar */}
      <Flex direction="column" w="250px" bg="red.500" color="white" p="20px" justifyContent="space-between">
        <Box>
          <Box mb="9" display="flex" flexDirection="column" alignItems="center" w="100%">
            <Image
              src="/img/esb.png"
              boxSize="120px"
              borderRadius="full"
              mb="4"
              border="3px solid white"
            />
          </Box>
          <Button onClick={() => router.push('/welcome')} leftIcon={<IoArrowBack />} bg="white" color="red.500" w="full" mb="10px">Back</Button>
          <Button onClick={() => router.push('/administration-dashboard')} leftIcon={<IoBarChart />} bg="white" color="red.500" w="full" mb="10px">Dashboard</Button>
          <Button onClick={() => router.push('/administration-chatbot')} leftIcon={<IoChatbubbles />} bg="white" color="red.500" w="full" mb="20px">Chatbot</Button>
        </Box>
        <Button onClick={handleLogout} leftIcon={<IoLogOut />} bg="white" color="red.500" w="full">Log Out</Button>
      </Flex>

      {/* Main Content */}
      <Flex flex="1" direction="column" bg="gray.100" p="20px" minH="0">
        {/* Header */}
        <Flex justifyContent="space-between" alignItems="center" mb="10px">
          <InputGroup w="300px">
            <InputLeftElement pointerEvents="none">
              <Icon as={IoSearch} color="gray.400" />
            </InputLeftElement>
            <Input placeholder="Search..." bg="white" borderRadius="md" />
          </InputGroup>
          <Flex alignItems="center" gap={3}>
            <Button colorScheme="red" variant="outline" onClick={onOpen}>Help</Button>
            <Menu>
              <MenuButton><Icon as={IoPersonCircle} w="40px" h="40px" color="gray.600" cursor="pointer" /></MenuButton>
              <MenuList>
                <MenuItem><Text fontWeight="bold">Admin User</Text></MenuItem>
              </MenuList>
            </Menu>
          </Flex>
        </Flex>
      {/* Help Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="white" borderRadius="xl" boxShadow="xl">
          <ModalHeader color="red.600" fontWeight="bold" fontSize="2xl" borderBottom="1px solid" borderColor="gray.200">Aide - Fonctionnalités du Chatbot</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="start" spacing={4} fontSize="md" color="gray.800">
              <Text fontWeight="semibold" fontSize="lg">Voici tout ce que je peux faire pour toi :</Text>
              <Text>📊 <b>Donne-moi le feedback chart.</b></Text>
              <Text>🟢🔴😐 <b>Afficher le détail des feedbacks positifs, négatifs ou neutres</b> sur une période donnée ou par matière.</Text>
              <Text>📈 <b>Afficher des graphiques</b> (camembert, barres, donut) pour toutes les matières ou une matière précise.</Text>
              <Text>⚖️ <b>Comparer plusieurs matières</b> sur leurs feedbacks (nombre, positifs, négatifs, neutres).</Text>
              <Text>🏆 <b>Afficher le top N matières</b> ayant reçu le plus de feedbacks sur une période.</Text>
              <Text>🤖 <b>Répondre à toutes tes questions</b> sur les statistiques de feedbacks étudiants.</Text>
              <Box pt={2}>
                <Text fontWeight="semibold" fontSize="md" mb={2}>Tu peux essayer par exemple :</Text>
                <VStack align="start" spacing={1} pl={2}>
                  <Text>👉 « Afficher les details de feedbacks positifs aujourd'hui. »</Text>
                  <Text>👉 « Afficher les details de feedbacks pour la matière machine learning. »</Text>
                  <Text>👉 « Donne-moi les feedbacks négatifs cette semaine. »</Text>
                  <Text>👉 « Affiche moi des graphiques pour la matiere machine learning et la matiere business.»</Text>
                  <Text>👉 « Donne-moi les graphiques des feedbacks pour la matière finance hier. »</Text>
                  <Text>👉 « Donne moi les top 3 matières de cette semaine. »</Text>
                  <Text>👉 « Donne-moi le chart comparatif des feedbacks par matière. »</Text>
                </VStack>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

        <Flex flex="1" overflow="hidden">
          {/* Chatbot Content */}
          <Flex flex="1" direction="column" alignItems="center" justifyContent="center" minH="0">
            <Box
              w="80%"
              h={isChatbotLarge ? "90vh" : "70%"}
              bg="white"
              borderRadius="md"
              boxShadow="md"
              p="20px"
              display="flex"
              flexDirection="column"
              minH="0"
              transition="height 0.3s"
              position="relative"
            >
              <Flex position="absolute" top="20px" right="20px" zIndex={2} justifyContent="flex-end">
                <Button
                  size="sm"
                  colorScheme="red"
                  borderRadius="full"
                  onClick={() => setIsChatbotLarge(v => !v)}
                  aria-label="Agrandir le chatbot"
                >
                  <Icon as={IoBarChart} boxSize={4} mr={1} />
                  <Text fontWeight="bold" fontSize="md">+</Text>
                </Button>
              </Flex>
              <Text fontSize="2xl" fontWeight="bold" mb="20px" color="red.500" textAlign="center" w="100%">Administration Chatbot</Text>
              <VStack spacing="10px" align="start" h="100%" flex="1" minH="0">
                <Box
                  ref={scrollRef}
                  w="100%"
                  flex="1"
                  bg="gray.50"
                  borderRadius="md"
                  overflowY="auto"
                  p="10px"
                  boxShadow="inner"
                  minH="0"
                  maxH="100%"
                >
                  {messages.map((msg, idx) => (
                    <Flex key={idx} justifyContent={msg.sender === 'bot' ? 'flex-start' : 'flex-end'} alignItems="flex-end" mb="5px">
                      {msg.sender === 'bot' && (
                        <Image src="/img/esb.png" boxSize="32px" borderRadius="full" mr="8px" border="2px solid #f87171" alt="Bot" />
                      )}
                      <Box bg={msg.sender === 'bot' ? 'red.100' : 'blue.100'} p="10px" borderRadius="md" maxW="70%">
                        {msg.sender === 'bot' ? (
                          (() => {
                            const backendUrl = 'http://127.0.0.1:5000';
                            let html = msg.text.replace(/\n/g, '<br />');
                            // Always rewrite /static/ URLs to backend
                            html = html.replace(/src=(['"])?\/?static\/(bar_total\.png|bar_stacked\.png|pie\.png)\1?/g, `src="${backendUrl}/static/$2"`);
                            return <Box as="span" dangerouslySetInnerHTML={{ __html: html }} fontSize="md" />;
                          })()
                        ) : (
                          <Text>{msg.text}</Text>
                        )}
                      </Box>
                      {msg.sender === 'bot' && (
                        <HStack spacing="5px" ml="10px">
                          <Icon as={IoCopy} w="16px" h="16px" color="gray.500" cursor="pointer" onClick={() => handleCopy(msg.text)} />
                          <Icon as={IoRefresh} w="16px" h="16px" color="gray.500" cursor="pointer" onClick={handleRefresh} />
                        </HStack>
                      )}
                      {msg.sender === 'user' && (
                        <Icon as={IoPersonCircle} w="32px" h="32px" color="#3b82f6" ml="8px" />
                      )}
                    </Flex>
                  ))}
                </Box>

                {/* Input Row */}
                <Flex w="100%" alignItems="center">
                  <Input
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSend();
                    }}
                    flex="1"
                    borderRadius="md"
                    bg="gray.50"
                  />
                  <Button
                    ml="10px"
                    colorScheme="red"
                    onClick={() => handleSend()}
                    p="0"
                    w="40px"
                    h="40px"
                    borderRadius="full"
                    isLoading={agentActive}
                  >
                    <Icon as={IoSend} w="20px" h="20px" />
                  </Button>
                </Flex>
              </VStack>
            </Box>
          </Flex>

          {/* Right Sidebar */}
          <Box w="300px" bg="white" borderRadius="md" boxShadow="md" p="20px" ml="20px">
            <Text fontSize="lg" fontWeight="bold" mb="10px" color="gray.700">Student Chat History</Text>
            <Box w="100%" maxH="70vh" overflowY="auto" mb="20px" p="2px">
              {allChats.length === 0 ? (
                <Text color="gray.400" fontStyle="italic">No chat history yet.</Text>
              ) : (
                // Group by user with explicit typing
                Object.entries(
                  allChats.reduce((acc: Record<string, any[]>, msg: any) => {
                    // Always group by username, fallback to 'user'
                    const uname = msg.username && msg.username !== msg.user_id ? msg.username : (msg.username || 'user');
                    if (!acc[uname]) acc[uname] = [];
                    acc[uname].push(msg);
                    return acc;
                  }, {})
                ).map(([uname, msgs]) => (
                  <Box key={uname} mb="12px">
                    <Button w="100%" colorScheme="red" variant="outline" mb="2px" onClick={() => { setSelectedUser(uname); setModalOpen(true); }}>{uname}</Button>
                    <Text fontSize="xs" color="gray.500">{(msgs as any[]).length} messages</Text>
                  </Box>
                ))
              )}
            </Box>
            {/* Modal for user chat history */}
            <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} size="md">
              <ModalOverlay />
              <ModalContent bg="white" borderRadius="xl" boxShadow="xl">
                <ModalHeader color="red.600" fontWeight="bold" fontSize="xl" borderBottom="1px solid" borderColor="gray.200">Chat History: {selectedUser}</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                  <Box w="100%" maxH="60vh" overflowY="auto" p="2px">
                    {selectedUser && allChats.filter(m => {
                      // Only show messages for selected username
                      const uname = m.username && m.username !== m.user_id ? m.username : (m.username || 'user');
                      return uname === selectedUser;
                    }).slice(-50).map((msg, idx) => (
                      <Flex key={msg._id || idx} direction="column" alignItems={msg.sender === 'bot' ? 'flex-start' : 'flex-end'} mb="10px">
                        <Text fontWeight="bold" fontSize="sm" color="gray.600" mb="2px">{msg.username && msg.username !== msg.user_id ? msg.username : (msg.username || 'user')}</Text>
                        <Box bg={msg.sender === 'bot' ? 'red.100' : 'blue.100'} p="10px" borderRadius="md" maxW="90%">
                          <Text fontSize="md">{msg.message || msg.text}</Text>
                        </Box>
                      </Flex>
                    ))}
                  </Box>
                </ModalBody>
              </ModalContent>
            </Modal>
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
}
